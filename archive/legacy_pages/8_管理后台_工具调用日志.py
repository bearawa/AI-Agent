import streamlit as st
import json
import pandas as pd
from repositories import sqlite_repository
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav

# 页面配置
st.set_page_config(
    page_title="工具调用日志 - AIZS 管理后台",
    page_icon="🛠️",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# Premium 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #7f8c8d;
        margin-bottom: 25px;
    }
    .log-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #eef2f3;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 12px;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
    }
    .badge-success { background-color: #2ecc71; }
    .badge-fail { background-color: #e74c3c; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🛠️ 工具调用审计日志</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">系统管理员可在此页面查看并审计 Agent 所有 Function Calling 工具执行轨迹，包含入参、执行耗时、成功状态及返回结果摘要。</p>', unsafe_allow_html=True)

# 侧边栏导航指示
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：工具调用日志")
render_logout_button()

# --- 筛选控制面板 ---
st.markdown("### 🔍 筛选条件")
with st.container():
    c1, c2, c3 = st.columns(3)
    
    with c1:
        tool_options = ["全部", "get_weather", "get_school_calendar", "get_campus_service_status", "search_campus_knowledge"]
        selected_tool = st.selectbox("选择工具：", tool_options)
        
    with c2:
        status_options = {"全部": None, "执行成功": 1, "执行失败": 0}
        selected_status_lbl = st.selectbox("执行状态：", list(status_options.keys()))
        selected_status_val = status_options[selected_status_lbl]
        
    with c3:
        limit_count = st.slider("最大读取条数：", 10, 200, 50)

# 执行数据库读取
tool_name_filter = None if selected_tool == "全部" else selected_tool
logs = sqlite_repository.list_tool_logs(limit=limit_count, tool_name=tool_name_filter, success=selected_status_val)

st.markdown("---")
st.markdown(f"### 📋 工具日志明细 (共 {len(logs)} 条记录)")

if not logs:
    st.info("💡 暂无符合筛选条件的工具调用日志。")
else:
    for idx, log in enumerate(logs):
        log_id = log["tool_log_id"]
        sess_id = log["session_id"] or "未知会话"
        msg_id = log["message_id"] or "尚未生成最终消息"
        t_name = log["tool_name"]
        t_disp = log["tool_display_name"] or t_name
        t_args = log["tool_args"]
        t_res = log["tool_result"]
        success = log["success"]
        err_msg = log["error_message"]
        elapsed = log["elapsed_ms"]
        created = log["created_at"]
        
        status_badge = '<span class="status-badge badge-success">成功</span>' if success == 1 else '<span class="status-badge badge-fail">失败</span>'
        
        # 截取提要
        card_title = f"⏱️ {created} | 工具：{t_disp} ({t_name}) | 耗时：{elapsed} ms"
        
        with st.expander(card_title):
            st.markdown(f"**日志 ID:** `{log_id}` | **关联会话 ID:** `{sess_id}`")
            st.markdown(f"**状态:** {status_badge}", unsafe_allow_html=True)
            if err_msg:
                st.error(f"**错误信息:** {err_msg}")
            
            c_args, c_res = st.columns(2)
            with c_args:
                st.markdown("**📥 传入参数 (Arguments)：**")
                try:
                    formatted_args = json.dumps(json.loads(t_args), indent=2, ensure_ascii=False)
                    st.code(formatted_args, language="json")
                except:
                    st.code(t_args, language="text")
                    
            with c_res:
                st.markdown("**📤 执出结果 (Result)：**")
                try:
                    formatted_res = json.dumps(json.loads(t_res), indent=2, ensure_ascii=False)
                    st.code(formatted_res, language="json")
                except:
                    st.code(t_res, language="text")
