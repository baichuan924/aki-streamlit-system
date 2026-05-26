"""报告生成与下载。"""
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent if CURRENT_FILE.parent.name == "pages" else CURRENT_FILE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import streamlit as st

from utils.data_store import (
    get_labs,
    get_medication,
    get_patient,
    get_prediction,
    init_session_state,
    render_page_header,
    render_section,
)
from utils.report import build_excel_bytes, build_text_report

st.set_page_config(page_title="报告导出", layout="wide")
init_session_state()
render_page_header("报告导出", "导出本次会话的肾损伤风险预测报告")

patient = get_patient()
labs = get_labs()
medication = get_medication()
prediction = get_prediction()

if not patient.get("patient_id"):
    st.warning("请先录入患者信息。")

record_id = st.session_state.get("last_record_id")
report_text = build_text_report(patient, labs, medication, prediction, record_id=record_id)

render_section("报告预览")
st.text_area("文本报告", value=report_text, height=380, disabled=True, label_visibility="collapsed")

render_section("导出")
pid = patient.get("patient_id", "draft")
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="下载文本报告 (.txt)",
        data=report_text.encode("utf-8"),
        file_name=f"aki_report_{pid}.txt",
        mime="text/plain",
        use_container_width=True,
    )

with col2:
    try:
        excel_bytes = build_excel_bytes(
            patient, labs, medication, prediction, record_id=record_id
        )
        st.download_button(
            label="下载 Excel 报告 (.xlsx)",
            data=excel_bytes,
            file_name=f"aki_report_{pid}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Excel 生成失败：{exc}")

if not prediction:
    st.info("尚未完成风险预测时，报告中的预测结果部分将标注为「尚未完成预测」。")
else:
    st.caption(
        f"当前风险：{prediction.get('risk_level', '—')} "
        f"（{prediction.get('risk_score', 0):.1%}）"
    )
