# 智能化精准给药辅助系统 / 肾损伤风险预测系统

基于 **Python + Streamlit** 的多页面临床数据录入与 AKI 风险预测演示系统。

## 功能流程

1. 患者信息录入  
2. 实验室指标录入  
3. 用药信息录入  
4. 肾损伤风险预测（模拟模型）  
5. 统计分析  
6. 报告导出  

## 项目结构

```
aki_streamlit_system/
├── app.py                          # 入口（Streamlit Cloud 主文件）
├── pages/                          # 多页面
├── utils/                          # 业务逻辑
├── data/
│   └── patient_records.csv.example # 空表模板（可提交 Git）
├── model/                          # 真实模型目录（待接入）
├── requirements.txt
├── runtime.txt                     # Python 版本（Cloud 可选）
├── .streamlit/config.toml
└── .gitignore
```

## 本地运行

```bash
cd aki_streamlit_system
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Community Cloud

1. 将本项目推送到 **GitHub**（不要提交 `.venv`、`__pycache__`、真实患者 CSV）。
2. 打开 [share.streamlit.io](https://share.streamlit.io)，使用 GitHub 登录。
3. 点击 **New app**，选择仓库与分支。
4. **Main file path** 填写：`app.py`
5. 点击 **Deploy**，等待构建完成即可获得公网 URL（手机/电脑浏览器均可访问）。

### 部署检查清单

| 项 | 说明 |
|----|------|
| 入口 | `app.py` |
| 依赖 | `requirements.txt`（streamlit、pandas、plotly、openpyxl） |
| 数据 | 仅提交 `data/patient_records.csv.example`；运行时数据勿入库 |
| 路径 | 全部使用相对路径（`Path(__file__).parent.parent`） |
| 密钥 | 使用 Cloud Secrets，勿提交 `.streamlit/secrets.toml` |

## 替换真实模型

参见 `model/README.md`，修改 `utils/predict.py` 中的预测函数即可。

## 免责声明

本系统为演示框架，模拟预测结果 **不能用于临床诊断或治疗决策**。
