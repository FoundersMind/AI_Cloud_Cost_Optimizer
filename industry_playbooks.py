"""
Industry-specific FinOps context — aligns LLM prompts with how enterprises
prioritize cloud spend (compliance, latency, data gravity, commitments).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from app_paths import data_path

INDUSTRY_IDS: List[str] = [
    "general",
    "fintech_payments",
    "healthcare_life_sciences",
    "retail_ecommerce",
    "saas_b2b",
    "media_gaming",
    "manufacturing_supply_chain",
    "public_sector",
]

_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "general": {
        "label": "General / Multi-industry",
        "summary": (
            "Balanced FinOps: tagging & showback, rightsizing, storage lifecycle, "
            "idle resources, commitment discounts where utilization is provable."
        ),
        "priorities": [
            "Cost allocation (tags, cost centers) and monthly anomaly review",
            "Compute: rightsizing, autoscaling, Graviton where compatible",
            "Data: tier-aware storage, lifecycle, compression, query pushdown",
            "Observability: log sampling, metric cardinality controls, retention SLAs",
            "Purchasing: Savings Plans / RIs for steady baseline; Spot for fault-tolerant batch",
        ],
        "constraints": "Assume production SLOs must be preserved; call out migration risk explicitly.",
        "kpis": ["unit_cost_per_transaction", "waste_percent_est", "commitment_coverage"],
    },
    "fintech_payments": {
        "label": "Fintech & payments",
        "summary": (
            "Low-latency, PCI-scoped zones, strong audit trails; optimize without weakening "
            "isolation of cardholder data or breaking settlement windows."
        ),
        "priorities": [
            "Network egress and cross-AZ: regional affinity, private connectivity, caching",
            "Databases: IOPS vs storage class; read scaling; backup retention vs compliance",
            "KMS/HSM-related spend: key rotation policy vs cost; consolidate keystores where safe",
            "PCI-boundary hygiene: avoid 'cheap' shared logging that breaks segmentation",
            "Batch risk/analytics on Spot with strict data masking outside CHD environments",
        ],
        "constraints": (
            "PCI-DSS style boundaries and auditability — prefer managed controls over ad-hoc cost cuts."
        ),
        "kpis": ["cost_per_payment", "auth_latency_p99_guardrail", "pci_scope_tco"],
    },
    "healthcare_life_sciences": {
        "label": "Healthcare & life sciences",
        "summary": (
            "PHI minimization, retention and access logging; cost-aware research pipelines "
            "and imaging data lakes without weakening patient privacy controls."
        ),
        "priorities": [
            "Object storage for imaging/genomics: Intelligent Tiering / archival with legal hold process",
            "Compute: burst HPC vs always-on clusters; segregate PHI workloads",
            "Observability: de-identified logs; shorter hot retention, colder archive",
            "Vendor-managed DBs vs self-managed when BAAs and patch burden matter",
            "DR/HA: right-size multi-region; distinguish regulatory minimum vs gold-plating",
        ],
        "constraints": (
            "HIPAA/GDPR-aligned handling patterns — do not recommend practices that weaken PHI boundaries."
        ),
        "kpis": ["cost_per_patient_episode_proxy", "phi_footprint_gb", "research_job_unit_cost"],
    },
    "retail_ecommerce": {
        "label": "Retail & e-commerce",
        "summary": (
            "Seasonal traffic, CDN and checkout latency, recommendations/search spend; "
            "optimize for peak efficiency and fulfillment data flows."
        ),
        "priorities": [
            "CDN & edge caching for PDP/PLP; image optimization and tiered media delivery",
            "Auto scale/catalog search tiers; cache hot facets; throttle non-critical batch",
            "Order pipeline: idempotent consumers; queue depth-driven scaling",
            "Snowflake vs warehouse spend if analytics duplicated in operational stores",
            "Returns/OMS integration: reduce cross-system replication costs",
        ],
        "constraints": "Peak-season reliability and checkout conversion are primary; flag campaign-time risks.",
        "kpis": ["cost_per_order", "caching_hit_rate", "peak_to_median_scale_ratio"],
    },
    "saas_b2b": {
        "label": "B2B SaaS",
        "summary": (
            "Tenant-aware efficiency: noisy neighbor containment, feature flags, "
            "multi-tenant DB patterns, and unit economics per customer segment."
        ),
        "priorities": [
            "Per-tenant metering and cost-to-serve visibility (FinOps + product)",
            "Database tenancy: silo vs bridge vs pool — cost vs isolation trade-offs",
            "Background jobs: fair queues; rate limits to cap tail tenants",
            "API gateway & WAF: bot/abuse controls that also reduce junk traffic cost",
            "Sandbox vs prod isolation to avoid paying production rates for trials",
        ],
        "constraints": "Enterprise SLAs and SSO/audit features are non-negotiable for many buyers.",
        "kpis": ["gross_margin_after_infra", "cost_per_active_tenant", "supporting_features_tco"],
    },
    "media_gaming": {
        "label": "Media & gaming",
        "summary": (
            "Egress-heavy, realtime workloads, user-generated content; optimize render/transcode "
            "pipelines and global distribution while preserving QoE."
        ),
        "priorities": [
            "Transcode ladders and spot fleets for batch; reserved for realtime pathways",
            "Origin shield / mid-tier caches to reduce origin egress",
            "UGC storage: lifecycle to cold; malware scanning costs vs upload paths",
            "Live ops: regional relays; minimize cross-region replication chatter",
            "Telemetry: sampled play analytics; careful with high-cardinality player dimensions",
        ],
        "constraints": "QoE (stall rate, input lag) beats marginal savings — quantify playback risk.",
        "kpis": ["cost_per_1000_hours_viewed", "egress_per_active_user", "transcode_minute_cost"],
    },
    "manufacturing_supply_chain": {
        "label": "Manufacturing & supply chain",
        "summary": (
            "OT/IT boundaries, edge telemetry, time-series historians, and ERP integrations; "
            "optimize ingest and twin simulation spend."
        ),
        "priorities": [
            "Edge aggregation before cloud ingest; compress OPC/telemetry frames",
            "Time-series DB retention vs granularity; rollups for long history",
            "Digital twin/simulation: burst GPU vs reserved; job scheduling for idle windows",
            "Partner data exchange: reduce duplicate ETL hops and multi-copy pipelines",
            "Backhaul networks: private links vs VPN cost/latency trade-offs",
        ],
        "constraints": "Safety and plant-floor availability constraints — avoid aggressive shutdown policies.",
        "kpis": ["cost_per_site", "telemetry_gb_per_day", "simulation_job_cost"],
    },
    "public_sector": {
        "label": "Public sector / regulated agencies",
        "summary": (
            "Procurement commitments, sovereign/region lock-in, transparency reporting; "
            "favor auditable controls and predictable spend profiles."
        ),
        "priorities": [
            "Reserved / committed use aligned to budget cycles and appropriations",
            "Strong tagging for program/grant reporting; guard against shadow projects",
            "Data residency: in-region services even if slightly more expensive",
            "Legacy SAP-style integrations: lift-and-optimize vs full redesign decisions",
            "Open standards and exportable billing artifacts for oversight bodies",
        ],
        "constraints": "Compliance and transparency often outweigh aggressive Spot usage.",
        "kpis": ["cost_per_citizen_served_proxy", "grant_attribution_accuracy", "commitment_utilization"],
    },
}


def get_playbook(industry_id: str) -> Dict[str, Any]:
    return _PLAYBOOKS.get(industry_id, _PLAYBOOKS["general"])


def load_selected_industry_id() -> str:
    p = data_path("industry_selection.json")
    if not os.path.isfile(p):
        return "general"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        vid = data.get("vertical_id") or data.get("industry_id")
        if isinstance(vid, str) and vid in INDUSTRY_IDS:
            return vid
    except (OSError, json.JSONDecodeError):
        pass
    return "general"


def playbook_prompt_block(industry_id: str) -> str:
    pb = get_playbook(industry_id)
    priorities = "\n".join(f"- {p}" for p in pb["priorities"])
    kpis = ", ".join(pb["kpis"])
    return (
        f"INDUSTRY_VERTICAL: {pb['label']}\n"
        f"INDUSTRY_SUMMARY: {pb['summary']}\n"
        f"STRATEGIC_PRIORITIES:\n{priorities}\n"
        f"COMPLIANCE_AND_CONSTRAINTS: {pb['constraints']}\n"
        f"SUGGESTED_KPI_FOCUS: {kpis}\n"
    )
