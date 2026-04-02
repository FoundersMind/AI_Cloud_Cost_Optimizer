"""
Enterprise FinOps dashboard: industry-aware prompts, synthetic billing lab, savings backlog.
Run from this folder:  streamlit run streamlit_app.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from app_paths import ROOT, data_path
from groq_llm import default_model
from industry_playbooks import INDUSTRY_IDS, get_playbook

load_dotenv(data_path(".env"))


def _apply_streamlit_secrets_to_environ() -> None:
    """Streamlit Community Cloud stores secrets in st.secrets; subprocesses only see os.environ."""
    try:
        secrets = st.secrets
    except (FileNotFoundError, RuntimeError, OSError):
        return
    for key in ("GROQ_API_KEY", "GROQ_MODEL"):
        try:
            val = secrets.get(key)
        except Exception:
            continue
        if val is not None and str(val).strip():
            os.environ[key] = str(val).strip()


st.set_page_config(
    page_title="FinOps Cost Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Must run after set_page_config (first Streamlit command); still before sidebar/pipeline.
_apply_streamlit_secrets_to_environ()


def _industry_label(vid: str) -> str:
    return get_playbook(vid)["label"]


def _save_industry(vertical_id: str) -> None:
    with open(data_path("industry_selection.json"), "w", encoding="utf-8") as f:
        json.dump({"vertical_id": vertical_id}, f, indent=2)


def _run_pipeline() -> Tuple[bool, str]:
    scripts = ["generate_profile.py", "generate_billing.py", "analyze_billing.py"]
    logs: List[str] = []
    for s in scripts:
        r = subprocess.run(
            [sys.executable, s],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        block = f"=== {s} (exit {r.returncode}) ===\n"
        if r.stdout:
            block += r.stdout
        if r.stderr:
            block += "\n--- stderr ---\n" + r.stderr
        logs.append(block)
        if r.returncode != 0:
            return False, "\n".join(logs)
    return True, "\n".join(logs)


def _load_report() -> Optional[Dict[str, Any]]:
    p = data_path("cost_optimization_report.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _load_billing_preview() -> Optional[List[Dict[str, Any]]]:
    p = data_path("mock_billing.json")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


st.title("Enterprise cloud cost intelligence")
st.caption(
    "Industry-specific FinOps playbooks steer the LLM toward strategic, practical initiatives. "
    "Billing remains synthetic unless you later plug in real CUR/exports."
)

with st.sidebar:
    st.header("Context")
    vertical = st.selectbox(
        "Industry vertical",
        options=INDUSTRY_IDS,
        format_func=_industry_label,
        index=0,
        help="Shapes synthetic billing mix and recommendation priorities (compliance, egress, commitments, etc.).",
    )
    pb = get_playbook(vertical)
    st.markdown(f"**Strategic focus:** {pb['summary']}")
    with st.expander("Vertical priorities"):
        for pr in pb["priorities"]:
            st.markdown(f"- {pr}")

    st.divider()
    if not os.getenv("GROQ_API_KEY"):
        st.warning("Set `GROQ_API_KEY` in `.env` ([Groq Console](https://console.groq.com/keys)).")
    else:
        st.success(f"Groq API key is set (model: `{default_model()}`).")

st.subheader("1) Workload description")
_path_desc = data_path("project_description.txt")
_default = ""
if os.path.isfile(_path_desc):
    _default = open(_path_desc, encoding="utf-8").read()
desc = st.text_area(
    "Project or portfolio description",
    value=_default,
    height=200,
    placeholder="Services, data volumes, regions, SLOs, compliance (PCI/HIPAA/etc.), monthly budget in INR…",
)

c1, c2, c3 = st.columns([1, 1, 1])
save_ctx = c1.button("Save context", type="secondary")
run_btn = c2.button("Run full analysis", type="primary")
refresh = c3.button("Reload dashboard")

pipeline_log = ""
if save_ctx:
    with open(_path_desc, "w", encoding="utf-8") as f:
        f.write(desc)
    _save_industry(vertical)
    st.success("Saved description and industry vertical.")

if run_btn:
    with open(_path_desc, "w", encoding="utf-8") as f:
        f.write(desc)
    _save_industry(vertical)
    with st.spinner("Running generate_profile → generate_billing → analyze_billing…"):
        ok, pipeline_log = _run_pipeline()
    if ok:
        st.success("Pipeline finished.")
    else:
        st.error("Pipeline failed — expand the log.")
    with st.expander("Pipeline log", expanded=not ok):
        st.code(pipeline_log or "(no output)", language="text")

if refresh:
    st.rerun()

report = _load_report()
if not report:
    st.info("Save context and run the analysis to generate `cost_optimization_report.json`.")
    st.stop()

meta = report.get("meta") or {}
if meta.get("industry_label"):
    st.caption(f"Report vertical: **{meta.get('industry_label')}**")

an = report.get("analysis", {})
su = report.get("summary", {})
m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly spend (INR)", f"₹{an.get('total_monthly_cost', 0):,.0f}")
m2.metric("Budget (INR)", f"₹{an.get('budget', 0):,.0f}")
var = float(an.get("budget_variance", 0) or 0)
if var > 0:
    m3.metric("Vs budget", f"₹{var:,.0f} over", delta=None)
elif var < 0:
    m3.metric("Vs budget", f"₹{abs(var):,.0f} under", delta=None)
else:
    m3.metric("Vs budget", "On target")
m4.metric("Backlog savings (INR)", f"₹{su.get('total_potential_savings', 0):,.0f}")

svc = an.get("service_costs") or {}
if svc:
    df_svc = pd.DataFrame([{"Service": k, "INR / mo": v} for k, v in svc.items()])
    df_svc = df_svc.sort_values("INR / mo", ascending=False)
    fig = px.bar(
        df_svc,
        x="Service",
        y="INR / mo",
        title="Spend by service (synthetic line items)",
    )
    fig.update_layout(xaxis_tickangle=-30, height=420)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Savings backlog")
recs = report.get("recommendations") or []
if not recs:
    st.warning("No recommendations in report.")
else:
    df_r = pd.DataFrame(recs)
    fc1, fc2 = st.columns(2)
    with fc1:
        if "implementation_effort" in df_r.columns:
            opts = sorted(df_r["implementation_effort"].dropna().unique().tolist())
            fe = st.multiselect("Effort", options=opts, default=opts)
            df_r = df_r[df_r["implementation_effort"].isin(fe)] if fe else df_r
    with fc2:
        if "risk_level" in df_r.columns:
            ro = sorted(df_r["risk_level"].dropna().unique().tolist())
            fr = st.multiselect("Risk", options=ro, default=ro)
            df_r = df_r[df_r["risk_level"].isin(fr)] if fr else df_r

    show_cols = [
        c
        for c in [
            "title",
            "service",
            "potential_savings",
            "recommendation_type",
            "strategic_theme",
            "finops_practice",
            "business_kpi_hint",
            "implementation_effort",
            "risk_level",
        ]
        if c in df_r.columns
    ]
    st.dataframe(
        df_r[show_cols].rename(
            columns={
                "title": "Initiative",
                "service": "Service",
                "potential_savings": "Savings ₹/mo",
                "recommendation_type": "Type",
                "strategic_theme": "Theme",
                "finops_practice": "FinOps practice",
                "business_kpi_hint": "KPI / value",
                "implementation_effort": "Effort",
                "risk_level": "Risk",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    for i, r in enumerate(recs[:5]):
        with st.expander(f"{i + 1}. {r.get('title', 'Initiative')}"):
            st.markdown(r.get("description", "_No description_"))
            steps = r.get("steps") or []
            if steps:
                st.markdown("**Steps**")
                for j, s in enumerate(steps, 1):
                    st.markdown(f"{j}. {s}")

st.download_button(
    "Download full report (JSON)",
    data=json.dumps(report, indent=2, ensure_ascii=False),
    file_name="cost_optimization_report.json",
    mime="application/json",
)

bill = _load_billing_preview()
if bill:
    with st.expander("Synthetic billing preview"):
        st.dataframe(pd.DataFrame(bill).head(40), use_container_width=True, hide_index=True)
