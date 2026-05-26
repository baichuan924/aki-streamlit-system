"""历史记录统计与 Plotly 可视化。"""
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent if CURRENT_FILE.parent.name == "pages" else CURRENT_FILE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_store import (
    get_labs,
    get_patient,
    get_prediction,
    init_session_state,
    load_records,
    render_page_header,
    render_section,
)
from utils.report import records_to_summary_df

st.set_page_config(page_title="统计分析", layout="wide")
init_session_state()
render_page_header("统计分析", "肾功能、感染指标与风险因素可视化")

patient = get_patient()
labs = get_labs()
prediction = get_prediction()

PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=40, r=20, t=40, b=40),
    font=dict(color="#334155"),
)


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=title, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(**PLOTLY_LAYOUT, height=320)
    return fig


render_section("当前会话 · 肾功能指标")
if labs.get("creatinine") is not None:
    renal_df = pd.DataFrame(
        {
            "指标": ["血清肌酐", "血尿素氮", "估算eGFR", "血钾"],
            "数值": [
                float(labs.get("creatinine", 0)),
                float(labs.get("bun", 0)),
                float(prediction.get("egfr", 0)) if prediction else 0,
                float(labs.get("potassium", 0)),
            ],
            "单位": ["mg/dL", "mg/dL", "mL/min", "mmol/L"],
        }
    )
    fig_renal = px.bar(
        renal_df,
        x="指标",
        y="数值",
        text="数值",
        color_discrete_sequence=["#0284c7"],
    )
    fig_renal.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_renal.update_layout(**PLOTLY_LAYOUT, height=340, yaxis_title="检测值")
    st.plotly_chart(fig_renal, use_container_width=True)
else:
    st.plotly_chart(_empty_fig("请先录入实验室指标"), use_container_width=True)

render_section("当前会话 · 感染指标")
if labs.get("wbc") is not None:
    infect_df = pd.DataFrame(
        {
            "指标": ["白细胞 WBC", "CRP", "PCT"],
            "数值": [
                float(labs.get("wbc", 0)),
                float(labs.get("crp", 0)),
                float(labs.get("pct", 0)),
            ],
        }
    )
    severity = patient.get("infection_severity", "无")
    fig_inf = go.Figure()
    fig_inf.add_trace(
        go.Bar(
            x=infect_df["指标"],
            y=infect_df["数值"],
            marker_color=["#0369a1", "#0ea5e9", "#38bdf8"],
            text=infect_df["数值"].round(2),
            textposition="outside",
        )
    )
    fig_inf.update_layout(
        **PLOTLY_LAYOUT,
        height=340,
        title=f"感染严重程度（临床录入）：{severity}",
        yaxis_title="检测值",
    )
    st.plotly_chart(fig_inf, use_container_width=True)
else:
    st.plotly_chart(_empty_fig("请先录入感染相关指标"), use_container_width=True)

render_section("当前会话 · 风险因素贡献")
if prediction and prediction.get("factor_contributions"):
    contrib = prediction["factor_contributions"]
    cdf = pd.DataFrame({"因素": list(contrib.keys()), "贡献": list(contrib.values())})
    fig_risk = px.bar(
        cdf,
        x="贡献",
        y="因素",
        orientation="h",
        color="贡献",
        color_continuous_scale=["#bae6fd", "#0284c7"],
    )
    fig_risk.update_layout(**PLOTLY_LAYOUT, height=max(280, len(cdf) * 40), coloraxis_showscale=False)
    st.plotly_chart(fig_risk, use_container_width=True)
elif prediction:
    st.info("本次预测未分解因素贡献明细。")
else:
    st.plotly_chart(_empty_fig("请先完成肾损伤风险预测"), use_container_width=True)

render_section("历史记录统计")
df = load_records()
summary = records_to_summary_df(df)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("CSV 记录总数", len(df))
with c2:
    high = (
        summary["risk_level"].astype(str).str.contains("高").sum()
        if not summary.empty and "risk_level" in summary.columns
        else 0
    )
    st.metric("高风险记录数", int(high))
with c3:
    if not summary.empty and "risk_score" in summary.columns:
        scores = pd.to_numeric(summary["risk_score"], errors="coerce").dropna()
        st.metric("历史平均风险", f"{scores.mean():.1%}" if len(scores) else "—")
    else:
        st.metric("历史平均风险", "—")

if not df.empty:
    if "risk_level" in summary.columns and summary["risk_level"].notna().any():
        level_counts = summary["risk_level"].value_counts().reset_index()
        level_counts.columns = ["风险等级", "数量"]
        fig_pie = px.pie(
            level_counts,
            names="风险等级",
            values="数量",
            hole=0.4,
            color_discrete_sequence=["#22c55e", "#eab308", "#ef4444", "#94a3b8"],
        )
        fig_pie.update_layout(**PLOTLY_LAYOUT, height=360)
        st.plotly_chart(fig_pie, use_container_width=True)

    if "risk_score" in summary.columns:
        scores = pd.to_numeric(summary["risk_score"], errors="coerce").dropna()
        if len(scores) > 0:
            fig_hist = px.histogram(
                scores,
                nbins=10,
                labels={"value": "风险概率"},
                color_discrete_sequence=["#0284c7"],
            )
            fig_hist.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)

    with st.expander("历史记录明细"):
        st.dataframe(summary, use_container_width=True, hide_index=True)
else:
    st.info("暂无 CSV 历史记录。完成预测后将自动写入 data/patient_records.csv。")
