"""用药信息录入。"""
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent if CURRENT_FILE.parent.name == "pages" else CURRENT_FILE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import streamlit as st

from utils.data_store import (
    get_medication,
    get_patient,
    init_session_state,
    render_data_panel,
    render_page_header,
    render_section,
    save_medication,
)
from utils.preprocess import NEPHROTOXIC_DRUG_OPTIONS, count_nephrotoxic_drugs, validate_medication

st.set_page_config(page_title="用药信息录入", layout="wide")
init_session_state()
render_page_header("用药信息录入", "记录主要用药及联合肾毒性药物")

if not get_patient().get("patient_id"):
    st.warning("请先在「患者信息录入」页面保存患者基本信息。")

existing = get_medication()
DRUG_OPTIONS = NEPHROTOXIC_DRUG_OPTIONS + ["其他"]

with st.form("medication_form"):
    render_section("主要用药")
    c1, c2 = st.columns(2)
    with c1:
        default_drug = existing.get("drug_name", DRUG_OPTIONS[0])
        if default_drug not in DRUG_OPTIONS:
            drug_idx = len(DRUG_OPTIONS) - 1
        else:
            drug_idx = DRUG_OPTIONS.index(default_drug)
        drug_select = st.selectbox("主要药物 *", DRUG_OPTIONS, index=drug_idx)
        drug_custom = ""
        if drug_select == "其他":
            drug_custom = st.text_input(
                "其他药物名称",
                value=existing.get("drug_name", "")
                if default_drug not in DRUG_OPTIONS
                else "",
            )
        daily_dose_mg = st.number_input(
            "日剂量 (mg)",
            min_value=0.0,
            value=float(existing.get("daily_dose_mg") or 1000.0),
            step=10.0,
        )
        nephrotoxic = st.checkbox("主药具有肾毒性", value=bool(existing.get("nephrotoxic", True)))
    with c2:
        route_opts = ["静脉滴注", "静脉注射", "口服", "肌注", "其他"]
        route = st.selectbox(
            "给药途径",
            route_opts,
            index=route_opts.index(existing.get("route", "静脉滴注"))
            if existing.get("route") in route_opts
            else 0,
        )
        freq_opts = ["q8h", "q12h", "qd", "bid", "tid", "其他"]
        frequency = st.selectbox(
            "给药频次",
            freq_opts,
            index=freq_opts.index(existing.get("frequency", "q12h"))
            if existing.get("frequency") in freq_opts
            else 1,
        )
        start_date = st.text_input(
            "开始日期",
            value=existing.get("start_date", ""),
            placeholder="YYYY-MM-DD",
        )
        duration_days = st.number_input(
            "预计疗程 (天)",
            min_value=1,
            value=int(existing.get("duration_days") or 7),
        )

    render_section("联合肾毒性药物")
    saved_drugs = existing.get("nephrotoxic_drugs") or []
    nephrotoxic_drugs = st.multiselect(
        "选择联合使用的肾毒性药物（可多选）",
        NEPHROTOXIC_DRUG_OPTIONS,
        default=[d for d in saved_drugs if d in NEPHROTOXIC_DRUG_OPTIONS],
        help="用于评估联合肾毒性暴露风险",
    )

    med_notes = st.text_area("用药备注", value=existing.get("med_notes", ""), height=60)

    submitted = st.form_submit_button("保存到会话", type="primary", use_container_width=True)

if submitted:
    final_drug = drug_custom.strip() if drug_select == "其他" else drug_select
    data = {
        "drug_name": final_drug,
        "nephrotoxic_drugs": nephrotoxic_drugs,
        "daily_dose_mg": daily_dose_mg,
        "route": route,
        "frequency": frequency,
        "start_date": start_date.strip(),
        "duration_days": duration_days,
        "nephrotoxic": nephrotoxic,
        "med_notes": med_notes.strip(),
    }
    errors = validate_medication(data)
    if errors:
        for e in errors:
            st.error(e)
    else:
        save_medication(data)
        n = count_nephrotoxic_drugs(data)
        st.success(f"用药信息已写入 st.session_state（肾毒性药物暴露计数：{n}）。")

med = get_medication()
if med:
    n = count_nephrotoxic_drugs(med)
    st.caption(f"当前联合肾毒性药物数量（含主药）：**{n}**")
render_data_panel("用药信息", med)
