# Multi-Cloud AI Cost Optimizer (FinOps Lab)

A learning-oriented tool that turns a **plain-language workload description** into **structured profile**, **synthetic billing line items**, and an **enterprise-style savings backlog**—using **Groq (LLM)**. It supports **AWS**, **Microsoft Azure**, and **Google Cloud** through **per-cloud prompt agents** (different billing shapes and FinOps language per provider).

> **Important:** Billing data is **synthetic** unless you plug in real exports (CUR, Azure Cost Management, GCP billing export). The app does **not** connect to your cloud accounts by default.

## What This Tool Does

- **Analyze** simulated spend against your stated **monthly budget (INR)**.
- **Route** generation and recommendations by **primary cloud**: AWS, Azure, or GCP.
- **Bias** scenarios with an **industry vertical** (fintech, healthcare, retail, etc.) via `industry_playbooks.py`.
- **Surface** recommendations with effort, risk, FinOps themes, and implementation steps.
- **Run** from a **Streamlit dashboard** or a **CLI** menu.

## Multi-Cloud “Agents”

Each provider uses a dedicated **agent** in code (`cloud_agents.py`): its own system prompt and billing schema (e.g. Azure ARM-style resources, GCP project/zone paths, AWS-style CUR line items).  

- **Streamlit:** Sidebar — **Primary cloud (agent routing)**.  
- **CLI:** Menu **0** — **Set primary cloud**.  

Selection is stored in **`cloud_selection.json`** (gitignored, like `industry_selection.json`). The profile step records **`primary_cloud_provider`** (`aws` | `azure` | `gcp`) in `project_profile.json`.

## System Architecture

```
Project Description + Industry + Cloud
        ↓
 Profile (LLM)  →  Synthetic billing (LLM, per-cloud agent)  →  Analysis + backlog (LLM)
        ↓                      ↓                                        ↓
 project_profile.json    mock_billing.json              cost_optimization_report.json
```

## Project Structure

```
├── streamlit_app.py           # Dashboard (Streamlit Cloud entry: this file)
├── cost_optimizer.py          # CLI menu (option 0 = cloud provider)
├── generate_profile.py        # Description → project_profile.json (+ primary_cloud_provider)
├── generate_billing.py        # Synthetic billing for active cloud agent
├── analyze_billing.py         # Cost rollup + Groq-backed recommendations
├── cloud_agents.py            # Per-cloud prompts, selection helpers, routing
├── groq_llm.py                # Groq API chat completions
├── industry_playbooks.py     # Industry-specific FinOps context
├── project_description.txt   # Input narrative (gitignored when generated)
├── project_profile.json       # Structured profile (gitignored)
├── cloud_selection.json      # aws | azure | gcp (gitignored)
├── industry_selection.json   # Vertical id (gitignored)
├── mock_billing.json         # Synthetic line items (gitignored)
├── cost_optimization_report.json
├── requirements.txt
└── README.md
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. **Create app** → repository and branch **main**.
4. **Main file path:** `streamlit_app.py`
5. **App settings (⋮) → Secrets** — see [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example):

   ```toml
   GROQ_API_KEY = "gsk_..."
   ```

   Optional:

   ```toml
   GROQ_MODEL = "llama-3.3-70b-versatile"
   ```

6. Deploy. Secrets are copied into `os.environ` on startup so subprocess steps can call the Groq API.

**Note:** Cloud storage is ephemeral; download JSON reports from the app if you need to keep them.

## Quick Start

### 1. Installation

```bash
git clone https://github.com/FoundersMind/AI_Cloud_Cost_Optimizer.git
cd AI_Cloud_Cost_Optimizer
pip install -r requirements.txt
```

### 2. Setup

Create a `.env` in the project folder (or use Streamlit secrets locally):

```env
GROQ_API_KEY=your_groq_key
# optional: GROQ_MODEL=llama-3.3-70b-versatile
```

Key: [Groq console](https://console.groq.com/keys).

### 3. Run the dashboard

```bash
streamlit run streamlit_app.py
```

In the sidebar, choose **industry vertical** and **primary cloud**, enter your workload narrative, then **Save context** and **Run full analysis**.

### 4. Run the CLI

```bash
python cost_optimizer.py
```

Use **0** to set **AWS / Azure / GCP**, then **2** for the full pipeline (`generate_profile` → `generate_billing` → `analyze_billing`).

## How to Use

### Step 1: Describe the workload

Include:

- What you are building and **which cloud** you use (or rely on the sidebar/CLI selection).
- **Tech stack** (compute, data, storage, observability).
- **Monthly budget in INR**, regions, SLOs, compliance (PCI, HIPAA, etc.) if relevant.

**Example (Azure fintech sketch):**

```
PCI-scoped payments API on Azure (East US + Central India). .NET on App Service,
Azure SQL vCore, Redis, Application Insights, Blob for receipts.
Budget ₹4,50,000/month, 99.9% uptime, long audit retention.
```

### Step 2: Run analysis

1. Extract **structured profile** (including `primary_cloud_provider`).
2. Generate **12–20 synthetic line items** in that cloud’s style (services, regions, `cost_inr`).
3. Compare totals to budget and produce **8–12 recommendations** (rightsizing, commitments, storage lifecycle, observability cost, tagging, etc.).

### Step 3: Review output

- **Streamlit:** KPIs, spend mix chart, filters, top initiatives, JSON download.
- **JSON report** `cost_optimization_report.json` includes **`meta.cloud_provider`** and **`meta.cloud_label`**.

## Types of Recommendations (examples)

Recommendations are LLM-generated and normalized to types such as: `open_source`, `optimization`, `right_sizing`, `commitment_discount`, `governance_tagging`, `observability_efficiency`, and others. Wording should match the **selected cloud** (e.g. Azure Hybrid Benefit / reservations, GCP CUDs, AWS Savings Plans / RIs).

## Sample CLI-style output

```
COST ANALYSIS SUMMARY
==================================================
Project: Payments API
Current Monthly Cost (INR): ...
Budget (INR): ...
Potential Savings (INR): ...
Report meta includes cloud_provider / cloud_label (e.g. azure / Microsoft Azure)
```

## Advanced Usage

### Run steps individually

```bash
python generate_profile.py
python generate_billing.py
python analyze_billing.py
```

Ensure `project_description.txt` exists and `cloud_selection.json` reflects your cloud before profile/billing if you rely on UI defaults.

### Export

- **Streamlit:** Download report JSON from the app.
- **CLI:** Menu **5** (JSON / text export).

## Learning Objectives

1. **Cloud cost awareness** — Budget vs spend, service mix, provider-native knobs.
2. **FinOps framing** — Effort, risk, KPI hints, chargeback / commitments.
3. **Multi-cloud literacy** — Same narrative; different SKU language per provider.
4. **Trade-offs** — Managed vs self-hosted, compliance vs cost (see industry playbooks).

## Technical Details

### Dependencies

- **groq** — LLM API  
- **streamlit**, **plotly** — Dashboard  
- **python-dotenv** — Local `.env`  
- **pandas** — Tables and charts  

### Model

- Default **GROQ_MODEL**: `llama-3.3-70b-versatile` (override in `.env` or secrets).

## Important Notes

1. **Synthetic billing** — For education and demos; not a substitute for real billing exports.
2. **Recommendations** — Suggestions only; validate against your architecture and compliance.
3. **Profile changes** — If upgrading from an older repo, re-run **generate_profile** so `primary_cloud_provider` exists.

## Contributing

Ideas: real billing ingestion (CUR / Azure / GCP), stronger validation of LLM JSON, tests, additional verticals or clouds.

## Additional Resources

- [AWS Well-Architected — Cost Optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
- [Azure Cost Management](https://learn.microsoft.com/en-us/azure/cost-management-billing/)
- [Google Cloud FinOps hub](https://cloud.google.com/learn/finops)

## Troubleshooting

1. **GROQ_API_KEY missing** — Set in `.env` or Streamlit **Secrets**.
2. **Could not load project data** — Run the full pipeline; ensure `project_profile.json` and `mock_billing.json` exist.
3. **Missing `primary_cloud_provider`** — Re-run `generate_profile.py` after pulling the latest code.

---

**Happy cost optimizing.** Use this to practice FinOps storytelling and provider-aware savings ideas—then validate with real usage and billing data.
