# 模型目录

本目录用于存放 **肾损伤风险预测** 的真实模型文件。

## 当前状态

第一版框架使用 `utils/predict.py` 中的 `mock_predict_aki_risk()` 作为占位预测函数，不依赖本目录下的模型文件。

## 后续接入真实模型

1. 将训练好的模型文件放入此目录，例如：
   - `aki_risk_model.pkl`（scikit-learn）
   - `model.onnx`（ONNX）
   - `weights.pt`（PyTorch，需自行编写加载逻辑）

2. 在 `utils/predict.py` 中新增加载与推理函数，例如：

```python
def load_model():
    import joblib
    return joblib.load("model/aki_risk_model.pkl")

def predict_aki_risk(patient, labs, medication):
    features = build_feature_vector(patient, labs, medication)
    # X = ...
    # return model.predict_proba(X)[0][1]
```

3. 在 `pages/4_肾损伤风险预测.py` 中将 `mock_predict_aki_risk` 替换为真实预测函数。

4. 建议在返回结果中保留与模拟函数一致的字段结构：
   - `risk_score`, `risk_level`, `egfr`, `key_factors`, `recommendations`, `model_version`

## 依赖说明

若模型需要额外库（如 `xgboost`、`torch`），请在项目根目录 `requirements.txt` 中补充对应版本。
