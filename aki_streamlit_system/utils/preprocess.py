"""数据校验与特征构建（供模拟/真实模型使用）。"""

from __future__ import annotations

from typing import Any

INFECTION_LEVELS = ["无", "轻度", "中度", "重度"]
NEPHROTOXIC_DRUG_OPTIONS = [
    "万古霉素",
    "氨基糖苷类",
    "造影剂",
    "NSAIDs",
    "ACEI/ARB",
    "利尿剂",
    "环孢素/他克莫司",
    "铂类化疗药",
]


def validate_patient(patient: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not patient.get("patient_id"):
        errors.append("请填写患者编号。")
    if patient.get("age") is not None and (patient["age"] < 0 or patient["age"] > 120):
        errors.append("年龄应在 0–120 岁之间。")
    if patient.get("weight_kg") is not None and patient["weight_kg"] <= 0:
        errors.append("体重应大于 0。")
    if patient.get("infection_severity") not in INFECTION_LEVELS:
        errors.append("请选择感染严重程度。")
    return errors


def validate_labs(labs: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if labs.get("creatinine") is None:
        errors.append("请填写血清肌酐。")
    elif labs["creatinine"] <= 0:
        errors.append("血清肌酐应大于 0。")
    if labs.get("bun") is not None and labs["bun"] < 0:
        errors.append("血尿素氮不能为负数。")
    return errors


def validate_medication(medication: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    drugs = medication.get("nephrotoxic_drugs") or []
    if not medication.get("drug_name") and not drugs:
        errors.append("请填写主要药物或选择联合肾毒性药物。")
    if medication.get("daily_dose_mg") is not None and medication["daily_dose_mg"] < 0:
        errors.append("日剂量不能为负数。")
    return errors


def estimate_egfr(creatinine: float, age: float, sex: str) -> float:
    """简化 CKD-EPI 风格估算（占位，非临床诊断用）。"""
    if creatinine <= 0 or age <= 0:
        return 90.0
    kappa = 0.7 if sex == "女" else 0.9
    alpha = -0.329 if sex == "女" else -0.411
    min_cr = min(creatinine / kappa, 1.0)
    max_cr = max(creatinine / kappa, 1.0)
    egfr = 141 * (min_cr ** alpha) * (max_cr ** -1.209) * (0.993 ** age)
    if sex == "女":
        egfr *= 1.018
    return round(max(5.0, min(egfr, 150.0)), 1)


def count_nephrotoxic_drugs(medication: dict[str, Any]) -> int:
    """统计联合肾毒性药物数量（含主药若具肾毒性）。"""
    selected = list(medication.get("nephrotoxic_drugs") or [])
    primary = medication.get("drug_name", "")
    if medication.get("nephrotoxic") and primary and primary not in selected:
        selected = [primary] + selected
    return len(set(selected))


def build_feature_vector(
    patient: dict[str, Any],
    labs: dict[str, Any],
    medication: dict[str, Any],
) -> dict[str, Any]:
    age = float(patient.get("age") or 60)
    weight = float(patient.get("weight_kg") or 70)
    height_cm = float(patient.get("height_cm") or 170)
    creatinine = float(labs.get("creatinine") or 1.0)
    bun = float(labs.get("bun") or 15)
    potassium = float(labs.get("potassium") or 4.0)
    wbc = float(labs.get("wbc") or 6.0)
    crp = float(labs.get("crp") or 5.0)
    pct = float(labs.get("pct") or 0.1)
    daily_dose = float(medication.get("daily_dose_mg") or 0)
    sex = patient.get("sex") or "男"
    egfr = estimate_egfr(creatinine, age, sex)
    dose_per_kg = daily_dose / weight if weight > 0 else 0.0
    bmi = weight / ((height_cm / 100) ** 2) if height_cm > 0 else 0.0

    return {
        "age": age,
        "weight_kg": weight,
        "height_cm": height_cm,
        "bmi": round(bmi, 1),
        "creatinine": creatinine,
        "bun": bun,
        "urea": bun,
        "potassium": potassium,
        "wbc": wbc,
        "crp": crp,
        "pct": pct,
        "egfr": egfr,
        "daily_dose_mg": daily_dose,
        "dose_per_kg": round(dose_per_kg, 4),
        "in_icu": bool(patient.get("in_icu")),
        "comorbidity_ckd": bool(patient.get("comorbidity_ckd")),
        "infection_severity": patient.get("infection_severity", "无"),
        "nephrotoxic_drug_count": count_nephrotoxic_drugs(medication),
    }
