"""患者基本信息录入。"""

from datetime import date, datetime

import streamlit as st

from utils.data_store import (
    clear_session_data,
    get_patient,
    init_session_state,
    render_data_panel,
    render_page_header,
    render_section,
    save_patient,
)
from utils.preprocess import INFECTION_LEVELS, validate_patient

st.set_page_config(page_title="患者信息录入", layout="wide")
init_session_state()
render_page_header("患者信息录入", "登记患者基本信息、ICU 状态及感染严重程度")

existing = get_patient()

with st.form("patient_form", clear_on_submit=False):
    render_section("基本信息")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        patient_id = st.text_input("患者编号 *", value=existing.get("patient_id", ""))
        name = st.text_input("姓名", value=existing.get("name", ""))
    with c2:
        sex_opts = ["男", "女", "其他"]
        sex = st.selectbox(
            "性别",
            sex_opts,
            index=sex_opts.index(existing.get("sex", "男"))
            if existing.get("sex") in sex_opts
            else 0,
        )
        age = st.number_input("年龄 *", min_value=0, max_value=120, value=int(existing.get("age") or 65))
    with c3:
        height_cm = st.number_input(
            "身高 (cm)",
            min_value=50.0,
            max_value=250.0,
            value=float(existing.get("height_cm") or 170.0),
            step=0.5,
        )
        weight_kg = st.number_input(
            "体重 (kg) *",
            min_value=0.0,
            max_value=300.0,
            value=float(existing.get("weight_kg") or 70.0),
            step=0.1,
        )
    with c4:
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 else 0
        st.metric("BMI（自动计算）", f"{bmi:.1f}" if bmi else "—")
        department = st.text_input("科室", value=existing.get("department", "肾内科"))
        ward = st.text_input("病区", value=existing.get("ward", ""))

    render_section("临床与风险因素")
    c5, c6, c7 = st.columns(3)
    with c5:
        diagnosis = st.text_input("主要诊断", value=existing.get("diagnosis", ""))
        _adm = existing.get("admission_date", "")
        try:
            _adm_date = datetime.strptime(_adm, "%Y-%m-%d").date() if _adm else date.today()
        except ValueError:
            _adm_date = date.today()
        admission_date = st.date_input("入院日期", value=_adm_date)
    with c6:
        inf_idx = (
            INFECTION_LEVELS.index(existing.get("infection_severity", "无"))
            if existing.get("infection_severity") in INFECTION_LEVELS
            else 0
        )
        infection_severity = st.selectbox(
            "感染严重程度 *",
            INFECTION_LEVELS,
            index=inf_idx,
            help="用于风险预测中的感染因素评估",
        )
        in_icu = st.checkbox("ICU 住院", value=bool(existing.get("in_icu")))
    with c7:
        comorbidity_ckd = st.checkbox("慢性肾病 (CKD)", value=bool(existing.get("comorbidity_ckd")))
        comorbidity_dm = st.checkbox("糖尿病", value=bool(existing.get("comorbidity_dm")))
        comorbidity_htn = st.checkbox("高血压", value=bool(existing.get("comorbidity_htn")))

    notes = st.text_area("备注", value=existing.get("notes", ""), height=72)

    c_btn1, c_btn2 = st.columns([3, 1])
    with c_btn1:
        submitted = st.form_submit_button("保存到会话", type="primary", use_container_width=True)
    with c_btn2:
        pass

if submitted:
    data = {
        "patient_id": patient_id.strip(),
        "name": name.strip(),
        "sex": sex,
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": round(bmi, 1),
        "department": department.strip(),
        "ward": ward.strip(),
        "diagnosis": diagnosis.strip(),
        "admission_date": str(admission_date) if admission_date else "",
        "infection_severity": infection_severity,
        "in_icu": in_icu,
        "comorbidity_ckd": comorbidity_ckd,
        "comorbidity_dm": comorbidity_dm,
        "comorbidity_htn": comorbidity_htn,
        "notes": notes.strip(),
    }
    errors = validate_patient(data)
    if errors:
        for e in errors:
            st.error(e)
    else:
        save_patient(data)
        st.success("患者信息已写入 st.session_state，可继续录入实验室指标。")

render_data_panel("患者信息", get_patient())

with st.sidebar:
    st.markdown("**会话操作**")
    if st.button("清空全部会话数据", use_container_width=True):
        clear_session_data()
        st.rerun()
