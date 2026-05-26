"""报告生成与导出。"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd

PATIENT_LABELS = {
    "patient_id": "患者编号",
    "name": "姓名",
    "sex": "性别",
    "age": "年龄",
    "height_cm": "身高(cm)",
    "weight_kg": "体重(kg)",
    "bmi": "BMI",
    "department": "科室",
    "ward": "病区",
    "in_icu": "ICU住院",
    "diagnosis": "主要诊断",
    "admission_date": "入院日期",
    "infection_severity": "感染严重程度",
    "comorbidity_ckd": "慢性肾病",
    "comorbidity_dm": "糖尿病",
    "comorbidity_htn": "高血压",
    "notes": "备注",
}

LAB_LABELS = {
    "creatinine": "血清肌酐 (mg/dL)",
    "bun": "血尿素氮 (mg/dL)",
    "potassium": "血钾 (mmol/L)",
    "sodium": "血钠 (mmol/L)",
    "wbc": "白细胞 (×10⁹/L)",
    "crp": "CRP (mg/L)",
    "pct": "PCT (ng/mL)",
    "urine_output_ml": "24h尿量 (mL)",
    "lab_time": "检验时间",
    "alt": "ALT (U/L)",
    "lab_notes": "检验备注",
}

MED_LABELS = {
    "drug_name": "主要药物",
    "nephrotoxic_drugs": "联合肾毒性药物",
    "daily_dose_mg": "日剂量 (mg)",
    "route": "给药途径",
    "frequency": "给药频次",
    "start_date": "开始日期",
    "duration_days": "疗程(天)",
    "nephrotoxic": "主药具肾毒性",
    "med_notes": "用药备注",
}


def _format_value(key: str, value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(str(v) for v in value) if value else "—"
    return str(value) if value is not None and value != "" else "—"


def _dict_to_rows(data: dict[str, Any], labels: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for key, label in labels.items():
        if key in data:
            rows.append({"项目": label, "内容": _format_value(key, data[key])})
    return rows


def build_text_report(
    patient: dict[str, Any],
    labs: dict[str, Any],
    medication: dict[str, Any],
    prediction: dict[str, Any] | None,
    record_id: str | None = None,
) -> str:
    lines = [
        "=" * 60,
        "  智能化精准给药辅助系统 · 肾损伤风险预测报告",
        "=" * 60,
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if record_id:
        lines.append(f"记录编号：{record_id}")

    lines.extend(["", "【患者信息】"])
    for row in _dict_to_rows(patient, PATIENT_LABELS):
        lines.append(f"  {row['项目']}：{row['内容']}")

    lines.extend(["", "【实验室指标】"])
    for row in _dict_to_rows(labs, LAB_LABELS):
        lines.append(f"  {row['项目']}：{row['内容']}")

    lines.extend(["", "【用药信息】"])
    for row in _dict_to_rows(medication, MED_LABELS):
        lines.append(f"  {row['项目']}：{row['内容']}")

    lines.extend(["", "【风险预测结果】"])
    if prediction:
        prob = prediction.get("risk_probability", prediction.get("risk_score"))
        lines.append(f"  肾损伤风险概率：{prob:.2%}" if isinstance(prob, (int, float)) else f"  肾损伤风险概率：{prob}")
        lines.append(f"  风险等级：{prediction.get('risk_level', '—')}")
        lines.append(f"  估算 eGFR：{prediction.get('egfr', '—')} mL/min/1.73m²")
        lines.append("  关键影响因素：")
        for f in prediction.get("key_factors", []):
            lines.append(f"    · {f}")
        lines.append("  辅助建议：")
        for r in prediction.get("recommendations", []):
            lines.append(f"    · {r}")
        lines.append(f"  模型版本：{prediction.get('model_version', '—')}")
        lines.append(f"  说明：{prediction.get('disclaimer', '')}")
    else:
        lines.append("  （尚未完成预测）")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def build_excel_bytes(
    patient: dict[str, Any],
    labs: dict[str, Any],
    medication: dict[str, Any],
    prediction: dict[str, Any] | None,
    record_id: str | None = None,
) -> bytes:
    buffer = io.BytesIO()
    meta = pd.DataFrame(
        [
            {"项目": "报告生成时间", "内容": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"项目": "记录编号", "内容": record_id or "—"},
            {"项目": "系统版本", "内容": "aki_streamlit_system v0.2"},
        ]
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        meta.to_excel(writer, sheet_name="报告信息", index=False)
        pd.DataFrame(_dict_to_rows(patient, PATIENT_LABELS)).to_excel(
            writer, sheet_name="患者信息", index=False
        )
        pd.DataFrame(_dict_to_rows(labs, LAB_LABELS)).to_excel(
            writer, sheet_name="实验室指标", index=False
        )
        pd.DataFrame(_dict_to_rows(medication, MED_LABELS)).to_excel(
            writer, sheet_name="用药信息", index=False
        )
        if prediction:
            pred_rows = [
                {"项目": "肾损伤风险概率", "内容": f"{prediction.get('risk_score', 0):.2%}"},
                {"项目": "风险等级", "内容": prediction.get("risk_level", "—")},
                {"项目": "估算 eGFR", "内容": f"{prediction.get('egfr', '—')} mL/min/1.73m²"},
                {"项目": "模型版本", "内容": prediction.get("model_version", "—")},
            ]
            pd.DataFrame(pred_rows).to_excel(writer, sheet_name="预测结果", index=False)
            pd.DataFrame(
                [{"影响因素": k} for k in prediction.get("key_factors", [])]
            ).to_excel(writer, sheet_name="影响因素", index=False)
            pd.DataFrame(
                [{"辅助建议": r} for r in prediction.get("recommendations", [])]
            ).to_excel(writer, sheet_name="辅助建议", index=False)
            contrib = prediction.get("factor_contributions") or {}
            if contrib:
                pd.DataFrame(
                    [{"因素": k, "贡献分值": v} for k, v in contrib.items()]
                ).to_excel(writer, sheet_name="风险贡献", index=False)
        else:
            pd.DataFrame([{"项目": "状态", "内容": "尚未完成预测"}]).to_excel(
                writer, sheet_name="预测结果", index=False
            )

    buffer.seek(0)
    return buffer.getvalue()


def records_to_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["record_id", "created_at", "risk_score", "risk_level"]
        )
    cols = [c for c in ["record_id", "created_at", "risk_score", "risk_level"] if c in df.columns]
    return df[cols].copy()
