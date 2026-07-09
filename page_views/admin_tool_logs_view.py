# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 工具调用日志视图
重构版：使用主题管理器和组件库提供企业级用户体验。
"""
import json
import streamlit as st
from repositories import sqlite_repository
from utils.display_utils import safe_text, safe_json_preview
from utils.ui_utils import render_page_header, render_empty_state
from themes.theme_manager import theme_manager

theme = theme_manager.current_theme
colors = theme["colors"]
spacing = theme["spacing"]
typography = theme["typography"]
radius = theme["radius"]


def render():
    render_page_header(
        "🛠️ 工具调用审计日志",
        "系统管理员可在此页面查看并审计 Agent 所有 Function Calling 工具执行轨迹，包含入参、执行耗时、成功状态及返回结果摘要。"
    )

    # ── 筛选控制面板 ──
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🔍 筛选条件</h3>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns(3)

        with c1:
            tool_options = [
                "全部",
                "get_weather_amap",
                "search_nearby_poi",
                "plan_route",
                "search_campus_knowledge"
            ]
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
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📋 工具日志明细 (共 {len(logs)} 条记录)</h3>", unsafe_allow_html=True)

    if not logs:
        render_empty_state(
            title="暂无符合条件的工具调用日志",
            description="Agent 执行工具调用后，日志将自动记录在此。",
            icon="🔌"
        )
    else:
        for idx, log in enumerate(logs):
            log_id = log["tool_log_id"]
            sess_id = safe_text(log["session_id"], "未知会话")
            t_name = log["tool_name"]
            t_disp = safe_text(log["tool_display_name"], t_name)
            t_args = log["tool_args"]
            t_res = log["tool_result"]
            success = log["success"]
            err_msg = log["error_message"]
            elapsed = log["elapsed_ms"]
            created = safe_text(log["created_at"], "暂无")

            status_badge = f'<span style="background:{colors["success"]};color:white;padding:4px 10px;border-radius:{radius["radius_base"]};font-size:{typography["font_size_xs"]};font-weight:{typography["font_weight_bold"]};">✅ 执行成功</span>' if success == 1 else f'<span style="background:{colors["error"]};color:white;padding:4px 10px;border-radius:{radius["radius_base"]};font-size:{typography["font_size_xs"]};font-weight:{typography["font_weight_bold"]};">❌ 执行失败</span>'

            card_title = f"⏱️ {created} | 工具：{t_disp} ({t_name}) | 耗时：{safe_text(elapsed, '暂无')} ms"

            with st.expander(card_title):
                st.markdown(f"**日志 ID:** `{log_id}` | **关联会话 ID:** `{sess_id}`")
                st.markdown(f"**状态:** {status_badge}", unsafe_allow_html=True)
                if err_msg:
                    st.error(f"**错误信息:** {err_msg}")

                c_args, c_res = st.columns(2)
                with c_args:
                    st.markdown(f"<h4 style='color:{colors['text_secondary']};'>📥 传入参数 (Arguments)</h4>", unsafe_allow_html=True)
                    preview_args = safe_json_preview(t_args, max_length=500)
                    if preview_args:
                        try:
                            formatted_args = json.dumps(json.loads(t_args), indent=2, ensure_ascii=False)
                            st.code(formatted_args, language="json")
                        except (json.JSONDecodeError, TypeError, ValueError):
                            st.code(safe_text(t_args, "无入参"), language="text")
                    else:
                        st.caption("无入参")

                with c_res:
                    st.markdown(f"<h4 style='color:{colors['text_secondary']};'>📤 执行结果 (Result)</h4>", unsafe_allow_html=True)
                    preview_res = safe_json_preview(t_res, max_length=500)
                    if preview_res:
                        try:
                            formatted_res = json.dumps(json.loads(t_res), indent=2, ensure_ascii=False)
                            st.code(formatted_res, language="json")
                        except (json.JSONDecodeError, TypeError, ValueError):
                            st.code(safe_text(t_res, "无出参"), language="text")
                    else:
                        st.caption("无出参")
