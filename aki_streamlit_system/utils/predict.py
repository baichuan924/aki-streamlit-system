"""肾损伤风险预测（当前为模拟函数，后续可替换为真实模型）。"""

from __future__ import annotations

from typing import Any

from utils.preprocess import build_feature_vector

INFECTION_SCORE = {"无": 0.0, "轻度": 0.06, "中度": 0.14, "重度": 0.22}


def mock_predict_aki_risk(
    patient: dict[str, Any],
    labs: dict[str, Any],
    medication: dict[str, Any],
) -> dict[str, Any]:
    """
    模拟 AKI 风险预测。

    综合考虑：年龄、肌酐、eGFR、尿素氮、ICU、慢性肾病、
    联合肾毒性药物、感染严重程度等因素。
    """
    features = build_feature_vector(patient, labs, medication)
    contributions: dict[str, float] = {}
    factors: list[str] = []

    score = 0.06

    age = features["age"]
    if age >= 75:
        contributions["高龄(≥75岁)"] = 0.09
        factors.append(f"高龄（{int(age)} 岁）")
    elif age >= 65:
        contributions["年龄(65-74岁)"] = 0.05
        factors.append(f"年龄偏大（{int(age)} 岁）")

    cr = features["creatinine"]
    if cr >= 2.0:
        contributions["肌酐显著升高"] = 0.22
        factors.append(f"血清肌酐显著升高（{cr} mg/dL）")
    elif cr >= 1.5:
        contributions["肌酐升高"] = 0.14
        factors.append(f"血清肌酐升高（{cr} mg/dL）")
    elif cr >= 1.2:
        contributions["肌酐临界升高"] = 0.06

    egfr = features["egfr"]
    if egfr < 30:
        contributions["eGFR<30"] = 0.20
        factors.append(f"估算 eGFR 严重降低（{egfr} mL/min/1.73m²）")
    elif egfr < 60:
        contributions["eGFR<60"] = 0.12
        factors.append(f"估算 eGFR 降低（{egfr} mL/min/1.73m²）")

    bun = features["bun"]
    if bun >= 40:
        contributions["尿素氮显著升高"] = 0.14
        factors.append(f"血尿素氮显著升高（{bun} mg/dL）")
    elif bun >= 20:
        contributions["尿素氮升高"] = 0.08
        factors.append(f"血尿素氮偏高（{bun} mg/dL）")

    if features["in_icu"]:
        contributions["ICU住院"] = 0.12
        factors.append("ICU 住院患者")

    if features["comorbidity_ckd"]:
        contributions["慢性肾病"] = 0.16
        factors.append("合并慢性肾病 (CKD)")

    n_count = int(features["nephrotoxic_drug_count"])
    if n_count >= 3:
        contributions["多种肾毒性药物"] = 0.20
        factors.append(f"联合 {n_count} 种肾毒性药物")
    elif n_count >= 2:
        contributions["联合肾毒性药物"] = 0.14
        factors.append(f"联合 {n_count} 种肾毒性药物")
    elif n_count >= 1:
        contributions["肾毒性药物暴露"] = 0.07
        factors.append("存在肾毒性药物暴露")

    infection = features["infection_severity"]
    inf_score = INFECTION_SCORE.get(str(infection), 0.0)
    if inf_score > 0:
        contributions[f"感染({infection})"] = inf_score
        factors.append(f"感染严重程度：{infection}")

    if features.get("crp", 0) >= 50:
        contributions["CRP升高"] = 0.06
        if "感染" not in "".join(factors):
            factors.append(f"CRP 升高（{features['crp']} mg/L）")
    if features.get("wbc", 0) >= 12:
        contributions["白细胞升高"] = 0.04

    if features["potassium"] >= 5.5:
        contributions["高钾血症"] = 0.05
        factors.append(f"血钾偏高（{features['potassium']} mmol/L）")

    if features["dose_per_kg"] >= 15:
        contributions["剂量偏高"] = 0.08
        factors.append("按体重折算的药物日剂量偏高")

    score += sum(contributions.values())
    score = min(0.98, max(0.03, round(score, 4)))

    if score < 0.35:
        level = "低风险"
        level_short = "低"
    elif score < 0.65:
        level = "中风险"
        level_short = "中"
    else:
        level = "高风险"
        level_short = "高"

    recommendations = _build_recommendations(level_short, features, medication, factors)

    sorted_contrib = dict(
        sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "risk_score": score,
        "risk_probability": score,
        "risk_level": level,
        "risk_level_short": level_short,
        "egfr": egfr,
        "features": features,
        "factor_contributions": sorted_contrib,
        "key_factors": factors or ["当前录入指标未见显著高危因素"],
        "recommendations": recommendations,
        "model_version": "mock-v0.2",
        "disclaimer": "本结果为模拟预测，仅供系统演示与教学，不能替代临床判断。",
    }


def _build_recommendations(
    level_short: str,
    features: dict[str, Any],
    medication: dict[str, Any],
    factors: list[str],
) -> list[str]:
    drug = medication.get("drug_name") or "当前方案"
    recs: list[str] = []

    if level_short == "高":
        recs.extend([
            f"建议尽快评估 {drug} 的肾毒性风险，必要时肾内科会诊。",
            "24 小时内复查血清肌酐、尿素氮、电解质及尿量。",
            "加强容量状态评估，避免肾灌注不足或容量负荷过重。",
        ])
    elif level_short == "中":
        recs.extend([
            f"建议在 24–48 小时内复查肾功能，并评估是否调整 {drug} 剂量或给药间隔。",
            "监测尿量、肌酐及尿素氮变化趋势。",
        ])
    else:
        recs.extend([
            f"可按常规方案继续观察 {drug}，维持定期肾功能复查。",
            "继续监测关键实验室指标变化。",
        ])

    if features.get("in_icu"):
        recs.append("ICU 患者建议结合血流动力学与每日肾功能监测制定给药方案。")
    if features.get("comorbidity_ckd"):
        recs.append("合并 CKD 者须按肾功能分层调整药物剂量，参考说明书或循证剂量建议。")
    if int(features.get("nephrotoxic_drug_count", 0)) >= 2:
        recs.append("存在多种肾毒性药物联用，建议逐一评估必要性并考虑替代方案。")
    if features.get("infection_severity") in ("中度", "重度"):
        recs.append("感染较重时须兼顾抗感染疗效与肾脏安全，注意药物相互作用。")
    if features.get("egfr", 90) < 60:
        recs.append(f"估算 eGFR 为 {features['egfr']} mL/min/1.73m²，请依据肾功能调整给药。")

    return recs
