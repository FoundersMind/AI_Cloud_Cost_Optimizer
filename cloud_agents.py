"""
Per-cloud FinOps agents: prompt personas and helpers for routing the pipeline
to AWS, Azure, or GCP-shaped synthetic billing and analysis.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

from app_paths import data_path

CLOUD_PROVIDER_IDS: Tuple[str, ...] = ("aws", "azure", "gcp")

CLOUD_LABELS: Dict[str, str] = {
    "aws": "Amazon Web Services (AWS)",
    "azure": "Microsoft Azure",
    "gcp": "Google Cloud Platform (GCP)",
}

CLOUD_AGENT_NAMES: Dict[str, str] = {
    "aws": "AWS Billing & Optimization Agent",
    "azure": "Azure Cost Management Agent",
    "gcp": "GCP FinOps Agent",
}


def normalize_cloud_provider(raw: str | None) -> str:
    if not raw or not isinstance(raw, str):
        return "aws"
    x = raw.strip().lower()
    if x in ("amazon", "amazon web services", "amazon_web_services"):
        return "aws"
    if x in ("microsoft azure", "msazure", "microsoft"):
        return "azure"
    if x in ("google", "google cloud", "gcp", "google_cloud_platform"):
        return "gcp"
    if x in CLOUD_PROVIDER_IDS:
        return x
    return "aws"


def load_selected_cloud_provider() -> str:
    p = data_path("cloud_selection.json")
    if not os.path.isfile(p):
        return "aws"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        cid = data.get("cloud_provider") or data.get("primary_cloud_provider")
        if isinstance(cid, str):
            return normalize_cloud_provider(cid)
    except (OSError, json.JSONDecodeError):
        pass
    return "aws"


def save_cloud_selection(cloud_provider: str) -> None:
    cid = normalize_cloud_provider(cloud_provider)
    with open(data_path("cloud_selection.json"), "w", encoding="utf-8") as f:
        json.dump({"cloud_provider": cid}, f, indent=2)


def provider_display_names(cloud_id: str) -> List[str]:
    cid = normalize_cloud_provider(cloud_id)
    if cid == "azure":
        return ["Azure"]
    if cid == "gcp":
        return ["Google Cloud", "GCP"]
    return ["AWS"]


def billing_system_prompt(cloud_id: str) -> str:
    cid = normalize_cloud_provider(cloud_id)
    if cid == "azure":
        return (
            "You are the Azure Cost Management agent. You generate realistic Azure consumption "
            "line items (VMs, Azure SQL, Blob/Files, Functions, App Service, Load Balancer, "
            "Application Insights, VPN/ExpressRoute, etc.) consistent with real world usage and billing CSV exports."
        )
    if cid == "gcp":
        return (
            "You are the GCP FinOps agent. You generate realistic Google Cloud billing detail "
            "(Compute Engine, Cloud SQL, GCS, Cloud Functions, GKE, Cloud Load Balancing, "
            "Cloud Logging/Monitoring, networking egress, etc.) as seen in BigQuery billing export rows."
        )
    return (
        "You are the AWS Cost & Usage Report agent. You generate realistic AWS line items "
        "(EC2, RDS, S3, Lambda, CloudWatch, ALB/NLB, CloudFront, data transfer, etc.) "
        "consistent with CUR-style billing."
    )


def billing_user_instructions(cloud_id: str, budget_inr: float) -> str:
    cid = normalize_cloud_provider(cloud_id)
    if cid == "azure":
        return f"""
TARGET CLOUD: Azure only. Every line item must use Azure service names and realistic Azure resource IDs
(e.g. /subscriptions/.../resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-api-01).

Each billing record must include ALL fields:
  - month (YYYY-MM)
  - service (Azure service, e.g. Virtual Machines, Azure SQL Database, Storage Accounts, Functions, Application Insights)
  - resource_id (Azure ARM-style path or logical name)
  - region (e.g. eastus, westeurope, centralindia)
  - usage_type (e.g. D-series VM Linux, DTU-based SQL, Hot LRS Blob)
  - usage_quantity (number)
  - unit (hours, GB, GB-month, requests, etc.)
  - cost_inr (INR; realistic vs budget)
  - desc (what the resource does)
  - cloud_provider: "azure"

Distribution (approximate): compute 40-50%, data platform 20-25%, object storage 10-15%,
networking 8-12%, monitoring/App Insights 5-8%, remainder other Azure services.

TOTAL BUDGET ANCHOR: ₹{budget_inr:,.0f} INR/month across line items (plausible variance).

OUTPUT: JSON array only. No markdown.
"""
    if cid == "gcp":
        return f"""
TARGET CLOUD: Google Cloud only. Use GCP service labels similar to billing export
(e.g. Compute Engine, Cloud SQL, Cloud Storage, Cloud Functions, Kubernetes Engine, Cloud Logging).

Each billing record must include ALL fields:
  - month (YYYY-MM)
  - service (GCP service name)
  - resource_id (projects/my-app/zones/asia-south1-a/instances/web-01 or bucket name, etc.)
  - region (e.g. asia-south1, us-central1, europe-west1)
  - usage_type (e.g. N2 standard instance core hours, Regional SSD PD, Standard storage class)
  - usage_quantity (number)
  - unit
  - cost_inr (INR; realistic vs budget)
  - desc
  - cloud_provider: "gcp"

Distribution: compute GCE/GKE ~40-50%, Cloud SQL ~20-25%, GCS ~10-15%,
networking/CDN ~8-12%, logging/monitoring ~5-8%, remainder other GCP.

TOTAL BUDGET ANCHOR: ₹{budget_inr:,.0f} INR/month.

OUTPUT: JSON array only. No markdown.
"""
    return f"""
TARGET CLOUD: AWS only. Use AWS service names (EC2, RDS, S3, Lambda, CloudWatch, ELB, CloudFront, etc.).

Each billing record must include ALL fields:
  - month (YYYY-MM)
  - service (AWS service)
  - resource_id (e.g. i-0abc123, db-..., bucket name)
  - region (e.g. ap-south-1, us-east-1)
  - usage_type (e.g. Linux/UNIX On-Demand, Standard storage)
  - usage_quantity (number)
  - unit
  - cost_inr (INR; realistic vs budget)
  - desc
  - cloud_provider: "aws"

Distribution: compute (EC2/Lambda) 40-50%, database (RDS) 20-25%, storage (S3) 10-15%,
network 8-12%, monitoring (CloudWatch) 5-8%, remainder other AWS.

TOTAL BUDGET ANCHOR: ₹{budget_inr:,.0f} INR/month.

OUTPUT: JSON array only. No markdown.
"""


def analysis_provider_context(cloud_id: str) -> str:
    cid = normalize_cloud_provider(cloud_id)
    if cid == "azure":
        return (
            "Primary cloud is Azure. Prefer Azure-native economics language: Reserved Instances, Savings Plans for compute "
            "(where applicable to Azure offers), Azure Hybrid Benefit, storage tiering (Hot/Cool/Archive), "
            "App Service plans, DTU/vCore SQL trade-offs, Log Analytics ingestion caps, egress discipline."
        )
    if cid == "gcp":
        return (
            "Primary cloud is Google Cloud. Prefer GCP economics: Committed Use Discounts (CUDs), SUDs where relevant, "
            "rightsizing machine types, Cloud SQL edition sizing, GCS autoclass vs lifecycle, "
            "BigQuery slot/cost controls, EDP/committed spend when discussing commitments, network service tiers."
        )
    return (
        "Primary cloud is AWS. Prefer AWS-native economics: Savings Plans, Reserved Instances, Spot for fault-tolerant workloads, "
        "RDS/Aurora I/O vs instance classes, S3 Intelligent-Tiering & lifecycle, Graviton where applicable, "
        "data transfer and NAT costs, CloudWatch logs/metrics cardinality."
    )


def build_billing_messages(
    profile: Dict[str, Any],
    industry_block: str,
    cloud_id: str,
) -> List[Dict[str, str]]:
    cid = normalize_cloud_provider(cloud_id)
    budget = float(profile.get("budget_inr_per_month") or 20000)
    user_body = f"""
Generate comprehensive synthetic billing data for this project.

PROJECT PROFILE:
{json.dumps(profile, indent=2)}

INDUSTRY_CONTEXT (bias cost drivers toward this vertical):
{industry_block}

ACTIVE_AGENT: {CLOUD_AGENT_NAMES[cid]}
CLOUD_CONTRACT: Only generate services and SKUs for {CLOUD_LABELS[cid]}. Do not mix other clouds in line items.

{billing_user_instructions(cid, budget)}

Generate 12-20 records.
"""
    return [
        {"role": "system", "content": billing_system_prompt(cid)},
        {"role": "user", "content": user_body.strip()},
    ]
