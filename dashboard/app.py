# ============================================================
# Harbinger — Streamlit Dashboard  (dashboard/app.py)
#
# Run with:
#   streamlit run dashboard/app.py
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from config.db_config import (
    SELECTIVITY_LEVELS, RUNS_PER_STATE, REGRESSION_THRESHOLD, TARGET_TABLE
)

# ─── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="Harbinger — Query Fragility Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 6px 0;
        border-left: 5px solid #7f7f7f;
    }
    .metric-card.critical { border-left-color: #e74c3c; }
    .metric-card.high     { border-left-color: #e67e22; }
    .metric-card.medium   { border-left-color: #f1c40f; }
    .metric-card.low      { border-left-color: #2ecc71; }
    .metric-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; margin-top: 4px; }
    .risk-critical { color: #e74c3c; }
    .risk-high     { color: #e67e22; }
    .risk-medium   { color: #f1c40f; }
    .risk-low      { color: #2ecc71; }
    .finding-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 12px;
        font-family: monospace;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/database-administrator.png", width=48)
    st.title("Harbinger")
    st.caption("PostgreSQL Query Fragility Engine")
    st.divider()

    st.subheader("Sweep Configuration")
    threshold = st.slider(
        "Regression Threshold (×)",
        min_value=1.2, max_value=5.0, value=float(REGRESSION_THRESHOLD), step=0.1,
        help="Slowdown multiplier above baseline that counts as a regression"
    )

    all_levels  = [5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 75, 100]
    sel_levels  = st.multiselect(
        "Selectivity Levels (%)",
        options=all_levels,
        default=[l for l in SELECTIVITY_LEVELS if l in all_levels],
        help="Which selectivity percentages to sweep"
    )

    runs = st.slider(
        "Runs per State",
        min_value=3, max_value=10, value=RUNS_PER_STATE,
        help="Warm-cache timing runs taken at each selectivity level"
    )

    save_results = st.checkbox("Auto-save CSV + JSON", value=True)
    st.divider()

    run_sweep = st.button("▶  Run Sweep", type="primary", use_container_width=True)
    st.caption(f"Table: `{TARGET_TABLE}`")

# ─── Main Layout ─────────────────────────────────────────────
st.title("🔍 Harbinger — Query Fragility Dashboard")
st.caption("Dual-Threshold PostgreSQL Performance & Plan Fragility Detection")

# ─── Session State ───────────────────────────────────────────
if "summary" not in st.session_state:
    st.session_state.summary = None
if "df" not in st.session_state:
    st.session_state.df = None

# ─── Run Sweep ───────────────────────────────────────────────
if run_sweep:
    if not sel_levels:
        st.error("Please select at least one selectivity level.")
        st.stop()

    with st.spinner("Running dual-threshold sweep — this takes ~3 minutes..."):
        import config.db_config as cfg
        orig_levels    = cfg.SELECTIVITY_LEVELS
        orig_runs      = cfg.RUNS_PER_STATE
        orig_threshold = cfg.REGRESSION_THRESHOLD

        cfg.SELECTIVITY_LEVELS   = sorted(sel_levels)
        cfg.RUNS_PER_STATE       = runs
        cfg.REGRESSION_THRESHOLD = threshold

        try:
            from scripts.harbinger_engine import run_full_sweep
            summary = run_full_sweep(regression_threshold=threshold, verbose=False)
            st.session_state.summary = summary

            # Build DataFrame
            rows = []
            for r in summary["results"]:
                rows.append({
                    "Selectivity (%)":  r["selectivity_pct"],
                    "Median (ms)":      r["median_ms"],
                    "Slowdown":         r["slowdown"],
                    "FT_runtime?":      "YES" if r["is_perf_regression"] else "—",
                    "PTT?":             "YES" if r["is_plan_transition"] else "—",
                })
            st.session_state.df = pd.DataFrame(rows)

            # Save if requested
            if save_results:
                import json, csv
                os.makedirs("results", exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_path  = f"results/sweep_{ts}.csv"
                json_path = f"results/sweep_{ts}.json"
                st.session_state.csv_path  = csv_path
                st.session_state.json_path = json_path

                with open(csv_path, 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(["selectivity_pct", "median_ms", "slowdown",
                                "is_perf_regression", "is_plan_transition"])
                    for r in summary["results"]:
                        w.writerow([r["selectivity_pct"], r["median_ms"], r["slowdown"],
                                    r["is_perf_regression"], r["is_plan_transition"]])

                clean_summary = {k: v for k, v in summary.items() if k != "results"}
                clean_summary["results"] = [
                    {k: v for k, v in r.items() if k != "plan_structure"}
                    for r in summary["results"]
                ]
                clean_summary["generated_at"] = datetime.now().isoformat()
                with open(json_path, 'w') as f:
                    json.dump(clean_summary, f, indent=2)

        except Exception as e:
            st.error(f"Sweep failed: {e}")
            st.stop()
        finally:
            cfg.SELECTIVITY_LEVELS   = orig_levels
            cfg.RUNS_PER_STATE       = orig_runs
            cfg.REGRESSION_THRESHOLD = orig_threshold

    st.success("Sweep complete!")

# ─── Display Results ─────────────────────────────────────────
summary = st.session_state.summary
df      = st.session_state.df

if summary is None:
    st.info("Configure the sweep in the sidebar and click **Run Sweep** to begin.")
    st.markdown("""
    ### How Harbinger Works

    ```
    SQL Query + Growing Table
          |
          v
    Drift Simulator (steps through selectivity levels)
          |
          v
    ┌──────────────────────────────────┐
    │   Dual-Threshold Engine          │
    │   ├── FT_runtime  (perf >= 2x)  │
    │   └── PTT         (plan change) │
    └──────────────────┬───────────────┘
                       |
                       v
              Risk Classification
          Critical / High / Medium / Low
    ```

    **FT_runtime** = first selectivity level where runtime >= Threshold × baseline  
    **PTT** = first selectivity level where execution plan type changes
    """)
    st.stop()

# ─── Metric Cards ────────────────────────────────────────────
ft   = summary.get("ft_runtime")
ptt  = summary.get("ptt")
risk = summary.get("risk_classification", "—")
base = summary.get("baseline_median_ms", 0)
case = "A" if (ft and ptt and ft < ptt) else ("B" if (ft and not ptt) else "—")

risk_cls = {
    "Critical Risk": "critical",
    "High Risk":     "high",
    "Medium Risk":   "medium",
    "Low Risk":      "low",
}.get(risk, "")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ft_display = f"{ft}%" if ft else "None"
    st.markdown(f"""
    <div class="metric-card {'critical' if ft and ft < 20 else 'high' if ft and ft < 40 else 'medium' if ft else 'low'}">
        <div class="metric-label">FT_runtime</div>
        <div class="metric-value">{ft_display}</div>
        <div style="color:#888;font-size:12px;margin-top:4px;">Performance Fragility Threshold</div>
    </div>""", unsafe_allow_html=True)

with col2:
    ptt_display = f"{ptt}%" if ptt else "None"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PTT</div>
        <div class="metric-value">{ptt_display}</div>
        <div style="color:#888;font-size:12px;margin-top:4px;">Plan Transition Threshold</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card {risk_cls}">
        <div class="metric-label">Risk Level</div>
        <div class="metric-value risk-{risk_cls}">{risk}</div>
        <div style="color:#888;font-size:12px;margin-top:4px;">Based on FT_runtime position</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Baseline</div>
        <div class="metric-value">{base:.3f} ms</div>
        <div style="color:#888;font-size:12px;margin-top:4px;">Median at 5% selectivity</div>
    </div>""", unsafe_allow_html=True)

# ─── Key Finding ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if ft and ptt and ft < ptt:
    finding = f"Case A — Performance degrades at {ft}% BEFORE plan changes at {ptt}%.  FT_runtime ({ft}%) < PTT ({ptt}%)"
elif ft and not ptt:
    finding = f"Case B — Performance degrades at {ft}% with NO plan transition detected. FT_runtime = {ft}% | PTT = None"
elif not ft:
    finding = "No regression detected across all selectivity levels."
else:
    finding = f"FT_runtime = {ft}% | PTT = {ptt}%"

st.markdown(f'<div class="finding-box">KEY FINDING: {finding}</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ─── Chart ───────────────────────────────────────────────────
st.subheader("Selectivity vs Runtime")

results = summary["results"]
x_vals  = [r["selectivity_pct"] for r in results]
y_vals  = [r["median_ms"]       for r in results]
s_vals  = [r["slowdown"]        for r in results]

# Colour each point by status
colors = []
for r in results:
    if r["is_plan_transition"]:
        colors.append("#9b59b6")   # purple = PTT
    elif r["is_perf_regression"]:
        colors.append("#e74c3c")   # red = regression
    else:
        colors.append("#2ecc71")   # green = safe

fig = go.Figure()

# Runtime line
fig.add_trace(go.Scatter(
    x=x_vals, y=y_vals,
    mode='lines+markers',
    name='Median Runtime (ms)',
    line=dict(color='#4a9eff', width=2.5),
    marker=dict(color=colors, size=10, line=dict(width=2, color='white')),
    hovertemplate='<b>%{x}% selectivity</b><br>Median: %{y:.3f} ms<br>Slowdown: %{customdata:.2f}x<extra></extra>',
    customdata=s_vals
))

# 2× threshold horizontal line
threshold_line = base * threshold
fig.add_hline(
    y=threshold_line,
    line_dash="dash",
    line_color="#f39c12",
    annotation_text=f"  {threshold:.1f}x threshold ({threshold_line:.2f} ms)",
    annotation_position="right",
    annotation_font_color="#f39c12"
)

# FT_runtime vertical line
if ft:
    fig.add_vline(
        x=ft,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"  FT_runtime = {ft}%",
        annotation_position="top right",
        annotation_font_color="#e74c3c"
    )

# PTT vertical line
if ptt:
    fig.add_vline(
        x=ptt,
        line_dash="dot",
        line_color="#9b59b6",
        annotation_text=f"  PTT = {ptt}%",
        annotation_position="top right",
        annotation_font_color="#9b59b6"
    )

fig.update_layout(
    paper_bgcolor='#0d1117',
    plot_bgcolor='#0d1117',
    font=dict(color='#c9d1d9', family='monospace'),
    xaxis=dict(
        title='Selectivity (%)',
        gridcolor='#21262d',
        tickvals=x_vals,
        ticktext=[f"{v}%" for v in x_vals]
    ),
    yaxis=dict(title='Median Runtime (ms)', gridcolor='#21262d'),
    legend=dict(bgcolor='#0d1117', bordercolor='#30363d', borderwidth=1),
    height=440,
    margin=dict(l=20, r=20, t=30, b=20),
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# ─── Results Table ───────────────────────────────────────────
st.subheader("Sweep Results Table")

def highlight_row(row):
    if row["FT_runtime?"] == "YES" and row["PTT?"] == "YES":
        return ['background-color: #2d1b69'] * len(row)
    elif row["PTT?"] == "YES":
        return ['background-color: #1f0f3d'] * len(row)
    elif row["FT_runtime?"] == "YES":
        return ['background-color: #3d0f0f'] * len(row)
    else:
        return [''] * len(row)

styled_df = df.style.apply(highlight_row, axis=1).format({
    "Median (ms)": "{:.3f}",
    "Slowdown":    "{:.2f}x"
})

st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ─── Legend ──────────────────────────────────────────────────
lcol1, lcol2, lcol3 = st.columns(3)
with lcol1:
    st.markdown("🟢 **Green marker** — Safe (< threshold)")
with lcol2:
    st.markdown("🔴 **Red marker** — Regression (FT_runtime)")
with lcol3:
    st.markdown("🟣 **Purple marker** — Plan transition (PTT)")

# ─── Download Buttons ────────────────────────────────────────
if save_results and hasattr(st.session_state, 'csv_path'):
    st.divider()
    st.subheader("Downloads")
    dl1, dl2 = st.columns(2)

    csv_path  = st.session_state.get("csv_path", "")
    json_path = st.session_state.get("json_path", "")

    if csv_path and os.path.exists(csv_path):
        with open(csv_path, 'rb') as f:
            dl1.download_button(
                "Download CSV",
                data=f.read(),
                file_name=os.path.basename(csv_path),
                mime="text/csv"
            )
    if json_path and os.path.exists(json_path):
        with open(json_path, 'rb') as f:
            dl2.download_button(
                "Download JSON",
                data=f.read(),
                file_name=os.path.basename(json_path),
                mime="application/json"
            )
