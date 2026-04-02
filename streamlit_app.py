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
import plotly.graph_objects as go
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


def _inject_ui_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Outfit', system-ui, sans-serif;
}

/* Ambient background */
[data-testid="stAppViewContainer"] > .main {
  background:
    radial-gradient(ellipse 120% 80% at 10% -20%, rgba(45, 212, 191, 0.12), transparent 50%),
    radial-gradient(ellipse 80% 60% at 95% 10%, rgba(139, 92, 246, 0.08), transparent 45%),
    linear-gradient(180deg, #080b10 0%, #0a1018 40%, #080b10 100%) !important;
}

.block-container {
  padding-top: 2rem !important;
  padding-bottom: 3rem !important;
  max-width: 1280px !important;
}

/* Headings */
h1 {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.03em !important;
  line-height: 1.15 !important;
  background: linear-gradient(135deg, #f0f4fc 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

h2, h3 {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
  color: #e8eef6 !important;
}

/* Hero panel */
.hero-wrap {
  border-radius: 16px;
  padding: 1.75rem 2rem;
  margin-bottom: 1.75rem;
  background: linear-gradient(145deg, rgba(17, 24, 32, 0.92) 0%, rgba(12, 18, 28, 0.88) 100%);
  border: 1px solid rgba(45, 212, 191, 0.22);
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.04) inset,
    0 24px 48px -12px rgba(0, 0, 0, 0.45);
}
.hero-kicker {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #2dd4bf;
  margin-bottom: 0.5rem;
}
.hero-title {
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #f8fafc;
  margin: 0 0 0.5rem 0;
  line-height: 1.2;
}
.hero-sub {
  color: #94a3b8;
  font-size: 1rem;
  line-height: 1.55;
  margin: 0;
  max-width: 52rem;
}

/* Section chrome */
.section-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 0.35rem;
}
.section-label-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2dd4bf;
  box-shadow: 0 0 12px rgba(45, 212, 191, 0.6);
}

/* Metric cards (Streamlit widgets) */
[data-testid="stMetric"] {
  background: linear-gradient(160deg, rgba(20, 28, 38, 0.95) 0%, rgba(14, 20, 30, 0.9) 100%);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 12px;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}
[data-testid="stMetric"] label {
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: #94a3b8 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1.35rem !important;
  font-weight: 500 !important;
  color: #f1f5f9 !important;
}

/* Inputs */
[data-testid="stTextArea"] textarea {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.88rem !important;
  border-radius: 12px !important;
  border: 1px solid rgba(45, 212, 191, 0.2) !important;
  background: rgba(10, 14, 22, 0.6) !important;
}

.stButton button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton button[kind="primary"] {
  background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%) !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(20, 184, 166, 0.35) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0c1118 0%, #0a0e14 100%) !important;
  border-right: 1px solid rgba(45, 212, 191, 0.1) !important;
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.5rem !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

/* Dividers & expanders */
hr {
  border: none;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  margin: 1.25rem 0;
}

.stAlert {
  border-radius: 12px !important;
  border: 1px solid rgba(148, 163, 184, 0.15) !important;
}

/* Footer / deploy */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* Spinner */
[data-testid="stSpinner"] {
  color: #2dd4bf !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
<div class="hero-wrap">
  <div class="hero-kicker">{kicker}</div>
  <p class="hero-title">{title}</p>
  <p class="hero-sub">{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def _section_title(label: str, title: str) -> None:
    st.markdown(
        f"""
<div class="section-label"><span class="section-label-dot"></span>{label}</div>
### {title}
        """,
        unsafe_allow_html=True,
    )


def _spend_chart(df_svc: pd.DataFrame) -> go.Figure:
    df_svc = df_svc.sort_values("INR / mo", ascending=True)
    teal = "#2dd4bf"
    bar_colors = [
        f"rgba(45, 212, 191, {0.35 + 0.55 * (i / max(len(df_svc) - 1, 1))})"
        for i in range(len(df_svc))
    ]
    fig = go.Figure(
        go.Bar(
            x=df_svc["INR / mo"],
            y=df_svc["Service"],
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"₹{v:,.0f}" for v in df_svc["INR / mo"]],
            textposition="outside",
            textfont=dict(size=11, color="#94a3b8", family="JetBrains Mono"),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}/mo<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(
            text="<b>Spend mix</b> <sup style='color:#64748b;font-weight:400'>synthetic line items</sup>",
            font=dict(size=17, color="#e8eef6", family="Outfit"),
            x=0,
            xanchor="left",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12, 18, 28, 0.5)",
        font=dict(family="Outfit", color="#94a3b8"),
        height=max(360, 44 * len(df_svc)),
        margin=dict(l=10, r=80, t=56, b=40),
        xaxis=dict(
            title="INR / month",
            gridcolor="rgba(148, 163, 184, 0.08)",
            zeroline=False,
            tickformat=",",
        ),
        yaxis=dict(title="", automargin=True, tickfont=dict(size=12)),
        showlegend=False,
    )
    return fig


def _effort_badge_css(effort: str) -> str:
    colors = {
        "low": ("#22c55e", "rgba(34, 197, 94, 0.15)"),
        "medium": ("#eab308", "rgba(234, 179, 8, 0.15)"),
        "high": ("#f97316", "rgba(249, 115, 22, 0.15)"),
    }
    fg, bg = colors.get((effort or "").lower(), ("#94a3b8", "rgba(148, 163, 184, 0.12)"))
    return f"color:{fg};background:{bg};padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;"


def _risk_badge_css(risk: str) -> str:
    colors = {
        "low": "#22c55e",
        "medium": "#eab308",
        "high": "#ef4444",
    }
    c = colors.get((risk or "").lower(), "#94a3b8")
    return f"color:{c};font-weight:600;font-size:0.75rem;"


st.set_page_config(
    page_title="FinOps Cost Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
_apply_streamlit_secrets_to_environ()
_inject_ui_styles()


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


_hero(
    "FinOps intelligence",
    "Cloud cost clarity that reads like a leadership brief.",
    "Describe your workload once—get industry-aware scenarios, spend breakdowns, and a prioritized savings backlog "
    "with effort, risk, and KPI language suited for stakeholder reviews. Synthetic billing until you wire real CUR/exports.",
)

with st.sidebar:
    st.markdown("### Context")
    vertical = st.selectbox(
        "Industry vertical",
        options=INDUSTRY_IDS,
        format_func=_industry_label,
        index=0,
        help="Shapes synthetic billing mix and recommendation priorities (compliance, egress, commitments, etc.).",
    )
    pb = get_playbook(vertical)
    st.markdown(
        f"<p style='color:#94a3b8;font-size:0.9rem;line-height:1.5;margin-top:0'>"
        f"<strong style='color:#e8eef6'>Strategic focus</strong><br>{pb['summary']}</p>",
        unsafe_allow_html=True,
    )
    with st.expander("Vertical priorities"):
        for pr in pb["priorities"]:
            st.markdown(f"· {pr}")

    st.markdown("---")
    if not os.getenv("GROQ_API_KEY"):
        st.warning("Add **GROQ_API_KEY** in `.env` or Streamlit **Secrets**.", icon="⚑")
    else:
        st.success(f"Model ready: `{default_model()}`", icon="✓")

_section_title("01 · Input", "Workload narrative")
_path_desc = data_path("project_description.txt")
_default = ""
if os.path.isfile(_path_desc):
    _default = open(_path_desc, encoding="utf-8").read()
desc = st.text_area(
    "Describe services, data volumes, regions, SLOs, compliance (PCI/HIPAA, etc.), monthly budget in INR",
    value=_default,
    height=200,
    label_visibility="collapsed",
    placeholder=(
        "Example: Fintech payments, ~2M tx/day, PCI scope, PostgreSQL + Redis, multi-AZ, "
        "₹X lakhs/month budget, cold DR in secondary region…"
    ),
)

c1, c2, c3 = st.columns([1, 1, 1])
save_ctx = c1.button("Save context", use_container_width=True)
run_btn = c2.button("Run full analysis", type="primary", use_container_width=True)
refresh = c3.button("Reload dashboard", use_container_width=True)

pipeline_log = ""
if save_ctx:
    with open(_path_desc, "w", encoding="utf-8") as f:
        f.write(desc)
    _save_industry(vertical)
    st.toast("Context saved.", icon="✓")

if run_btn:
    with open(_path_desc, "w", encoding="utf-8") as f:
        f.write(desc)
    _save_industry(vertical)
    with st.status("Running pipeline…", expanded=True) as status:
        st.write("**generate_profile** → structured profile")
        st.write("**generate_billing** → synthetic line items")
        st.write("**analyze_billing** → Groq-backed backlog")
        ok, pipeline_log = _run_pipeline()
        if ok:
            status.update(label="Pipeline complete", state="complete", expanded=False)
        else:
            status.update(label="Pipeline failed", state="error", expanded=True)
    if ok:
        st.toast("Analysis complete.", icon="✓")
    else:
        st.error("One or more steps failed. Review the log below.")
    with st.expander("Technical log", expanded=not ok):
        st.code(pipeline_log or "(no output)", language="text")

if refresh:
    st.rerun()

report = _load_report()
if not report:
    st.markdown(
        """
<div style="
  margin-top:2rem;
  padding:2.5rem 2rem;
  text-align:center;
  border-radius:16px;
  border:1px dashed rgba(45, 212, 191, 0.25);
  background: rgba(17, 24, 32, 0.4);
">
  <p style="color:#94a3b8;font-size:1.05rem;margin:0;max-width:36rem;margin-left:auto;margin-right:auto;">
    <strong style="color:#e8eef6">No report yet.</strong><br>
    Save your context and run <strong>Run full analysis</strong> to generate <code style="color:#2dd4bf">cost_optimization_report.json</code>.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

meta = report.get("meta") or {}
_meta_line = ""
if meta.get("industry_label"):
    _meta_line = meta.get("industry_label", "")

_section_title("02 · Executive snapshot", "KPIs & spend shape")
if _meta_line:
    st.caption(f"Report vertical · **{_meta_line}**")

an = report.get("analysis", {})
su = report.get("summary", {})
m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly spend", f"₹{an.get('total_monthly_cost', 0):,.0f}")
m2.metric("Budget", f"₹{an.get('budget', 0):,.0f}")
var = float(an.get("budget_variance", 0) or 0)
if var > 0:
    m3.metric("Vs budget", f"₹{var:,.0f} over")
elif var < 0:
    m3.metric("Vs budget", f"₹{abs(var):,.0f} under")
else:
    m3.metric("Vs budget", "On target")
savings_pct = su.get("savings_percentage", 0) or 0
m4.metric("Backlog savings", f"₹{su.get('total_potential_savings', 0):,.0f}", delta=f"~{savings_pct:.0f}% of spend")

svc = an.get("service_costs") or {}
if svc:
    df_svc = pd.DataFrame([{"Service": k, "INR / mo": float(v)} for k, v in svc.items()])
    st.plotly_chart(_spend_chart(df_svc), use_container_width=True)

_section_title("03 · Savings backlog", "Initiatives & drill-down")
recs = report.get("recommendations") or []
if not recs:
    st.warning("No recommendations in this report.")
else:
    df_r = pd.DataFrame(recs)
    fc1, fc2 = st.columns(2)
    with fc1:
        if "implementation_effort" in df_r.columns:
            opts = sorted(df_r["implementation_effort"].dropna().unique().tolist())
            fe = st.multiselect("Filter · effort", options=opts, default=opts)
            df_r = df_r[df_r["implementation_effort"].isin(fe)] if fe else df_r
    with fc2:
        if "risk_level" in df_r.columns:
            ro = sorted(df_r["risk_level"].dropna().unique().tolist())
            fr = st.multiselect("Filter · risk", options=ro, default=ro)
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
        height=min(520, 44 + 36 * len(df_r)),
    )

    st.markdown("**Top initiatives**")
    for i, r in enumerate(recs[:6]):
        effort = str(r.get("implementation_effort", "") or "")
        risk = str(r.get("risk_level", "") or "")
        save_amt = float(r.get("potential_savings", 0) or 0)
        with st.expander(f"**{i + 1}.** {r.get('title', 'Initiative')} · ₹{save_amt:,.0f}/mo"):
            ec1, ec2, ec3 = st.columns([1, 1, 2])
            with ec1:
                st.markdown(f"<span style='{_effort_badge_css(effort)}'>{effort.upper()} effort</span>", unsafe_allow_html=True)
            with ec2:
                st.markdown(f"<span style='{_risk_badge_css(risk)}'>Risk: {risk.upper()}</span>", unsafe_allow_html=True)
            with ec3:
                st.caption(f"{r.get('service', '')} · {r.get('recommendation_type', '')}")
            st.markdown(r.get("description", "_No description._"))
            steps = r.get("steps") or []
            if steps:
                st.markdown("**Execution checklist**")
                for j, s in enumerate(steps, 1):
                    st.markdown(f"{j}. {s}")

dl1, dl2 = st.columns([1, 3])
with dl1:
    st.download_button(
        "Export report (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="cost_optimization_report.json",
        mime="application/json",
        use_container_width=True,
    )

bill = _load_billing_preview()
if bill:
    with st.expander("Synthetic billing · first rows", expanded=False):
        st.dataframe(pd.DataFrame(bill).head(40), use_container_width=True, hide_index=True)
