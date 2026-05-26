"""智能化精准给药辅助系统 / 肾损伤风险预测系统 — 主页。"""

import streamlit as st

from utils.data_store import data_completion_status, init_session_state, render_page_header

st.set_page_config(
    page_title="肾损伤风险预测系统",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="auto",
)

init_session_state()
render_page_header(
    "智能化精准给药辅助系统",
    "肾损伤风险预测 · 临床数据录入与决策支持（演示版）",
)

st.markdown('<p class="medical-section-title">系统流程</p>', unsafe_allow_html=True)

steps = [
    ("1", "患者信息录入", "登记基本信息与合并症"),
    ("2", "实验室指标录入", "录入肌酐、尿素氮等检验结果"),
    ("3", "用药信息录入", "记录拟用或正在使用的药物"),
    ("4", "肾损伤风险预测", "基于当前数据运行风险预测（模拟模型）"),
    ("5", "统计分析", "查看历史预测记录与分布"),
    ("6", "报告导出", "导出 TXT / Excel 报告"),
]

# 两行三列，手机端通过 CSS 自动折行为单列
for row_start in (0, 3):
    cols = st.columns(3)
    for col, step in zip(cols, steps[row_start : row_start + 3]):
        num, title, desc = step
        with col:
            st.markdown(
                f"""
                <div class="medical-card">
                    <div style="font-size:1.5rem;color:#0ea5e9;font-weight:700;">{num}</div>
                    <div style="font-weight:600;color:#0f172a;">{title}</div>
                    <div style="font-size:0.85rem;color:#64748b;margin-top:0.25rem;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown('<p class="medical-section-title">当前会话进度</p>', unsafe_allow_html=True)
status = data_completion_status()
labels = list(status.keys())
done_flags = list(status.values())
for row_start in (0, 2):
    cols = st.columns(2)
    for col, label, done in zip(cols, labels[row_start : row_start + 2], done_flags[row_start : row_start + 2]):
        with col:
            icon = "✅" if done else "⏳"
            st.metric(label, "已完成" if done else "待完成", delta=icon)

if st.session_state.get("csv_write_disabled"):
    st.caption("提示：当前环境可能无法持久化写入 CSV，预测记录仍保存在本次会话中。")

st.info(
    "请使用左侧导航栏（手机端可点左上角展开）依次完成各页面录入。"
    "预测模块为 **模拟函数**，不能替代临床判断。"
)

with st.expander("使用说明"):
    st.markdown(
        """
        1. 在 **患者信息** 页面保存基本信息。
        2. 在 **实验室指标** 与 **用药信息** 页面补充检验与处方数据。
        3. 进入 **肾损伤风险预测** 执行预测并查看结果。
        4. 在 **统计分析** 查看历史记录与图表。
        5. 在 **报告导出** 下载 TXT 或 Excel 报告。
        """
    )
