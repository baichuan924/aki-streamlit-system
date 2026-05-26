"""会话状态与本地 CSV 数据持久化。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# 相对项目根目录的路径（兼容本地与 Streamlit Cloud）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RECORDS_CSV = DATA_DIR / "patient_records.csv"
RECORDS_CSV_EXAMPLE = DATA_DIR / "patient_records.csv.example"

CSV_COLUMNS = [
    "record_id",
    "created_at",
    "patient_json",
    "labs_json",
    "medication_json",
    "risk_score",
    "risk_level",
    "prediction_json",
]


def apply_medical_theme() -> None:
    """注入医疗数据系统风格的简洁白底样式。"""
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f8fafc;
        }
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e2e8f0;
        }
        .medical-header {
            background: linear-gradient(90deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .medical-header h1, .medical-header p {
            color: white !important;
            margin: 0;
        }
        .medical-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .medical-section-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #0f172a;
            border-left: 4px solid #0ea5e9;
            padding-left: 0.6rem;
            margin: 1rem 0 0.75rem 0;
        }
        .risk-badge-low { color: #15803d; font-weight: 700; }
        .risk-badge-medium { color: #ca8a04; font-weight: 700; }
        .risk-badge-high { color: #dc2626; font-weight: 700; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.5rem;
        }
        /* 自适应宽屏 / 手机，不固定最大宽度 */
        .main .block-container {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        @media (max-width: 768px) {
            .medical-header h1 {
                font-size: 1.25rem !important;
            }
            .medical-header p {
                font-size: 0.85rem !important;
            }
            div[data-testid="column"] {
                min-width: 0;
            }
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.5rem;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "") -> None:
    apply_medical_theme()
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="medical-header">
            <h1>{title}</h1>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str) -> None:
    st.markdown(f'<p class="medical-section-title">{title}</p>', unsafe_allow_html=True)


def render_data_panel(label: str, data: dict[str, Any]) -> None:
    """侧边或展开区展示 session 数据摘要。"""
    if not data:
        st.caption(f"{label}：暂无数据")
        return
    with st.expander(f"已保存 · {label}", expanded=False):
        st.json(data)


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "patient": {},
        "labs": {},
        "medication": {},
        "prediction": None,
        "last_record_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ensure_data_dir() -> None:
    """确保 data 目录与 CSV 存在（云端只读文件系统时由会话内存兜底）。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if RECORDS_CSV.exists():
        return
    if RECORDS_CSV_EXAMPLE.exists():
        RECORDS_CSV.write_bytes(RECORDS_CSV_EXAMPLE.read_bytes())
        return
    pd.DataFrame(columns=CSV_COLUMNS).to_csv(RECORDS_CSV, index=False, encoding="utf-8-sig")


def _read_csv_safe() -> pd.DataFrame:
    ensure_data_dir()
    if not RECORDS_CSV.exists() or RECORDS_CSV.stat().st_size == 0:
        return pd.DataFrame(columns=CSV_COLUMNS)
    try:
        return pd.read_csv(RECORDS_CSV, encoding="utf-8-sig")
    except (pd.errors.EmptyDataError, FileNotFoundError, OSError):
        return pd.DataFrame(columns=CSV_COLUMNS)


def _append_session_record(row: dict[str, Any]) -> None:
    history: list[dict[str, Any]] = list(st.session_state.get("records_history", []))
    history.append(row)
    st.session_state.records_history = history


def _records_from_session() -> pd.DataFrame:
    history = st.session_state.get("records_history", [])
    if not history:
        return pd.DataFrame(columns=CSV_COLUMNS)
    return pd.DataFrame(history)


def save_patient(data: dict[str, Any]) -> None:
    init_session_state()
    st.session_state.patient = data


def save_labs(data: dict[str, Any]) -> None:
    init_session_state()
    st.session_state.labs = data


def save_medication(data: dict[str, Any]) -> None:
    init_session_state()
    st.session_state.medication = data


def save_prediction(result: dict[str, Any]) -> None:
    init_session_state()
    st.session_state.prediction = result


def get_patient() -> dict[str, Any]:
    init_session_state()
    return dict(st.session_state.patient or {})


def get_labs() -> dict[str, Any]:
    init_session_state()
    return dict(st.session_state.labs or {})


def get_medication() -> dict[str, Any]:
    init_session_state()
    return dict(st.session_state.medication or {})


def get_prediction() -> dict[str, Any] | None:
    init_session_state()
    pred = st.session_state.prediction
    return dict(pred) if pred else None


def get_all_data() -> dict[str, Any]:
    return {
        "patient": get_patient(),
        "labs": get_labs(),
        "medication": get_medication(),
        "prediction": get_prediction(),
    }


def data_completion_status() -> dict[str, bool]:
    patient = get_patient()
    labs = get_labs()
    medication = get_medication()
    prediction = get_prediction()
    has_med = bool(medication.get("drug_name")) or bool(medication.get("nephrotoxic_drugs"))
    return {
        "患者信息": bool(patient.get("patient_id")),
        "实验室指标": labs.get("creatinine") is not None,
        "用药信息": has_med,
        "风险预测": prediction is not None,
    }


def clear_session_data() -> None:
    """清空当前会话录入（保留历史 CSV）。"""
    st.session_state.patient = {}
    st.session_state.labs = {}
    st.session_state.medication = {}
    st.session_state.prediction = None
    st.session_state.last_record_id = None


def append_record(
    patient: dict[str, Any],
    labs: dict[str, Any],
    medication: dict[str, Any],
    prediction: dict[str, Any],
) -> str:
    init_session_state()
    record_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    row = {
        "record_id": record_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "patient_json": json.dumps(patient, ensure_ascii=False),
        "labs_json": json.dumps(labs, ensure_ascii=False),
        "medication_json": json.dumps(medication, ensure_ascii=False),
        "risk_score": prediction.get("risk_score"),
        "risk_level": prediction.get("risk_level"),
        "prediction_json": json.dumps(prediction, ensure_ascii=False),
    }
    _append_session_record(row)
    try:
        ensure_data_dir()
        df = _read_csv_safe()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(RECORDS_CSV, index=False, encoding="utf-8-sig")
    except OSError:
        st.session_state.csv_write_disabled = True
    st.session_state.last_record_id = record_id
    return record_id


def load_records() -> pd.DataFrame:
    """合并磁盘 CSV 与会话内记录（云端重启后会话记录会清空）。"""
    init_session_state()
    df = _read_csv_safe()
    session_df = _records_from_session()
    if session_df.empty:
        return df
    if df.empty:
        return session_df
    combined = pd.concat([df, session_df], ignore_index=True)
    return combined.drop_duplicates(subset=["record_id"], keep="last")
