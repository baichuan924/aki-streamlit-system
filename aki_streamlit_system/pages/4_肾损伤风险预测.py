"""肾损伤风险预测与结果展示。"""

import plotly.graph_objects as go
import streamlit as st

from utils.data_store import (
    append_record,
    get_labs,
    get_medication,
    get_patient,
    get_prediction,
    init_session_state,
    render_page_header,
    render_section,
    save_prediction,
)
from utils.predict import mock_predict_aki_risk
from utils.preprocess import validate_labs, validate_medication, validate_patient

st.set_page_config(page_title="肾损伤风险预测", layout="wide")
init_session_state()
render_page_header("肾损伤风险预测", "基于会话数据运行模拟预测（未接入真实模型）")

patient = get_patient()
labs = get_labs()
medication = get_medication()

missing = []
if not patient.get("patient_id"):
    missing.append("患者信息")
if labs.get("creatinine") is None:
    missing.append("实验室指标")
if not medication.get("drug_name") and not medication.get("nephrotoxic_drugs"):
    missing.append("用药信息")

if missing:
    st.warning(f"请先完成：{'、'.join(missing)}。")
else:
    render_section("录入数据摘要")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("患者", patient.get("patient_id", "—"))
    with c2:
        st.metric("肌酐", f"{labs.get('creatinine', '—')} mg/dL")
    with c3:
        st.metric("尿素氮", f"{labs.get('bun', '—')} mg/dL")
    with c4:
        icu_txt = "是" if patient.get("in_icu") else "否"
        st.metric("ICU / 感染", f"{icu_txt} / {patient.get('infection_severity', '无')}")

    if st.button("运行模拟预测", type="primary", use_container_width=True):
        errors = (
            validate_patient(patient)
            + validate_labs(labs)
            + validate_medication(medication)
        )
        if errors:
            for e in errors:
                st.error(e)
        else:
            result = mock_predict_aki_risk(patient, labs, medication)
            save_prediction(result)
            record_id = append_record(patient, labs, medication, result)
            st.success(f"预测完成，结果已保存至会话与 CSV（{record_id}）。")

prediction = get_prediction()
if prediction:
    render_section("预测结果")
    score = float(prediction.get("risk_probability", prediction.get("risk_score", 0)))
    level = prediction.get("risk_level", "—")
    level_short = prediction.get("risk_level_short", "低")
    badge = {"低": "low", "中": "medium", "高": "high"}.get(level_short, "low")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("肾损伤风险概率", f"{score:.1%}")
    with m2:
        st.markdown(
            f'<p style="margin:0;color:#64748b;font-size:0.85rem;">风险等级</p>'
            f'<p class="risk-badge-{badge}" style="font-size:1.25rem;margin:0;">{level}</p>',
            unsafe_allow_html=True,
        )
    with m3:
        st.metric("估算 eGFR", f"{prediction.get('egfr', '—')} mL/min/1.73m²")
    with m4:
        st.metric("模型版本", prediction.get("model_version", "—"))

    st.caption(prediction.get("disclaimer", ""))

    col_gauge, col_factors = st.columns([1, 1])
    with col_gauge:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score * 100,
                number={"suffix": "%", "font": {"size": 28}},
                title={"text": "肾损伤风险概率"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#0284c7", "thickness": 0.25},
                    "bgcolor": "#f1f5f9",
                    "steps": [
                        {"range": [0, 35], "color": "#ecfdf5"},
                        {"range": [35, 65], "color": "#fefce8"},
                        {"range": [65, 100], "color": "#fef2f2"},
                    ],
                    "threshold": {
                        "line": {"color": "#0f172a", "width": 2},
                        "thickness": 0.8,
                        "value": score * 100,
                    },
                },
            )
        )
        fig.update_layout(
            height=300,
            margin=dict(l=24, r=24, t=48, b=16),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_factors:
        st.markdown("**关键影响因素**")
        for factor in prediction.get("key_factors", []):
            st.markdown(f"- {factor}")
        st.markdown("**辅助建议**")
        for rec in prediction.get("recommendations", []):
            st.markdown(f"- {rec}")

    contrib = prediction.get("factor_contributions") or {}
    if contrib:
        render_section("风险因素贡献（模拟）")
        import pandas as pd

        cdf = pd.DataFrame(
            {"因素": list(contrib.keys()), "贡献分值": list(contrib.values())}
        )
        fig_bar = go.Figure(
            go.Bar(
                x=cdf["贡献分值"],
                y=cdf["因素"],
                orientation="h",
                marker_color="#0ea5e9",
            )
        )
        fig_bar.update_layout(
            height=max(220, len(cdf) * 36),
            margin=dict(l=20, r=20, t=24, b=20),
            xaxis_title="贡献分值",
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("特征向量（供真实模型对接）"):
        st.json(prediction.get("features", {}))
