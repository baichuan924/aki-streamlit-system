"""实验室检验指标录入。"""

import streamlit as st

from utils.data_store import (
    get_labs,
    get_patient,
    init_session_state,
    render_data_panel,
    render_page_header,
    render_section,
    save_labs,
)
from utils.preprocess import estimate_egfr, validate_labs

st.set_page_config(page_title="实验室指标录入", layout="wide")
init_session_state()
render_page_header("实验室指标录入", "录入肾功能、感染相关指标及电解质")

patient = get_patient()
if not patient.get("patient_id"):
    st.warning("请先在「患者信息录入」页面保存患者基本信息。")

existing = get_labs()

with st.form("labs_form"):
    render_section("肾功能指标")
    c1, c2, c3 = st.columns(3)
    with c1:
        creatinine = st.number_input(
            "血清肌酐 (mg/dL) *",
            min_value=0.0,
            max_value=20.0,
            value=float(existing.get("creatinine") or 1.0),
            step=0.01,
            format="%.2f",
        )
        bun = st.number_input(
            "血尿素氮 / 尿素 (mg/dL) *",
            min_value=0.0,
            max_value=200.0,
            value=float(existing.get("bun") or 15.0),
            step=0.1,
            help="用于模拟预测中的尿素氮因素",
        )
    with c2:
        potassium = st.number_input(
            "血钾 (mmol/L)",
            min_value=0.0,
            max_value=10.0,
            value=float(existing.get("potassium") or 4.0),
            step=0.1,
        )
        sodium = st.number_input(
            "血钠 (mmol/L)",
            min_value=100.0,
            max_value=180.0,
            value=float(existing.get("sodium") or 140.0),
            step=0.5,
        )
    with c3:
        urine_output_ml = st.number_input(
            "24 小时尿量 (mL)",
            min_value=0,
            max_value=10000,
            value=int(existing.get("urine_output_ml") or 1500),
            step=50,
        )
        if patient.get("age") and creatinine > 0:
            egfr_preview = estimate_egfr(
                creatinine, float(patient.get("age", 60)), patient.get("sex", "男")
            )
            st.metric("估算 eGFR（预览）", f"{egfr_preview} mL/min/1.73m²")
        else:
            st.metric("估算 eGFR（预览）", "需先保存患者信息")

    render_section("感染相关指标")
    c4, c5, c6 = st.columns(3)
    with c4:
        wbc = st.number_input(
            "白细胞 WBC (×10⁹/L)",
            min_value=0.0,
            max_value=100.0,
            value=float(existing.get("wbc") or 6.0),
            step=0.1,
        )
    with c5:
        crp = st.number_input(
            "C 反应蛋白 CRP (mg/L)",
            min_value=0.0,
            max_value=500.0,
            value=float(existing.get("crp") or 5.0),
            step=0.5,
        )
    with c6:
        pct = st.number_input(
            "降钙素原 PCT (ng/mL)",
            min_value=0.0,
            max_value=100.0,
            value=float(existing.get("pct") or 0.1),
            step=0.01,
            format="%.2f",
        )

    render_section("其他")
    c7, c8 = st.columns(2)
    with c7:
        lab_time = st.text_input(
            "检验时间",
            value=existing.get("lab_time", ""),
            placeholder="如 2026-05-26 08:00",
        )
        alt = st.number_input(
            "ALT (U/L)",
            min_value=0.0,
            value=float(existing.get("alt") or 25.0),
            step=1.0,
        )
    with c8:
        lab_notes = st.text_area("检验备注", value=existing.get("lab_notes", ""), height=88)

    submitted = st.form_submit_button("保存到会话", type="primary", use_container_width=True)

if submitted:
    data = {
        "creatinine": creatinine,
        "bun": bun,
        "potassium": potassium,
        "sodium": sodium,
        "urine_output_ml": urine_output_ml,
        "wbc": wbc,
        "crp": crp,
        "pct": pct,
        "lab_time": lab_time.strip(),
        "alt": alt,
        "lab_notes": lab_notes.strip(),
    }
    errors = validate_labs(data)
    if errors:
        for e in errors:
            st.error(e)
    else:
        save_labs(data)
        st.success("实验室指标已写入 st.session_state。")

render_data_panel("实验室指标", get_labs())
