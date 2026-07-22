# -*- coding: utf-8 -*-
"""
AIZS｜统一门户控制中心入口
系统统一通过 streamlit run app.py 启动，内部采用状态机控制分流与权限校验。
重构版：使用主题管理器和组件库提供企业级用户体验。
"""
import streamlit as st
import time
from config import settings
from repositories import sqlite_repository
from utils.logger import logger
from utils.ui_utils import inject_global_css, render_nav_footer
from themes.theme_manager import theme_manager

# 1. 启动时执行数据库表初始化，保证第一次运行应用时库表就绪
try:
    sqlite_repository.init_db()
except Exception as e:
    logger.error(f"应用启动初始化 SQLite 数据库失败: {e}")

# 2. 页面全局配置设定 (在 app.py 头部仅调用一次)
st.set_page_config(
    page_title="AIZS｜中南财经政法大学 智能咨询平台",
    page_icon="🏫",
    layout="wide"
)

# 3. 注入全局 CSS 样式
inject_global_css()

# 4. 初始化会话状态
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "home"

if "user_page" not in st.session_state:
    st.session_state.user_page = "chat"

if "admin_page" not in st.session_state:
    st.session_state.admin_page = "knowledge_center"

# 获取主题配置
theme = theme_manager.current_theme
colors = theme["colors"]
spacing = theme["spacing"]
typography = theme["typography"]
radius = theme["radius"]

# --- 模式一：Home 统一门户首页 ---
if st.session_state.app_mode == "home":
    # 注入 CSS 隐藏侧边栏
    st.markdown(
        f'''
        <style>
        [data-testid="stSidebar"] {{
            display: none !important;
        }}
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
        .aizs-brand-header {{
            text-align: center;
            padding: {spacing["spacing_xxl"]} {spacing["spacing_lg"]};
            background: {colors["bg_card"]};
            border: 1px solid {colors["border"]};
            border-radius: {radius["radius_xl"]};
            margin-bottom: {spacing["spacing_md"]};
            color: {colors["text_primary"]};
        }}
        .aizs-brand-header h1 {{
            font-size: 2.5rem;
            font-weight: {typography["font_weight_bold"]};
            margin-bottom: {spacing["spacing_sm"]};
            color: {colors["text_primary"]};
        }}
        .aizs-brand-header p {{
            font-size: 1.1rem;
            color: {colors["text_secondary"]};
            margin-bottom: {spacing["spacing_base"]};
        }}
        .aizs-brand-tags {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: {spacing["spacing_sm"]};
        }}
        .aizs-brand-tag {{
            background: {colors["bg_hover"]};
            color: {colors["text_secondary"]};
            border: 1px solid {colors["border_light"]};
            padding: {spacing["spacing_xs"]} {spacing["spacing_base"]};
            border-radius: {radius["radius_round"]};
            font-size: {typography["font_size_xs"]};
        }}
        .aizs-entry-card {{
            background: {colors["bg_card"]};
            padding: {spacing["spacing_lg"]};
            border-radius: {radius["radius_lg"]};
            box-shadow: {colors["shadow_card"]};
            transition: all {theme["transitions"]["transition_base"]};
        }}
        .aizs-entry-card:hover {{
            transform: translateY(-4px);
            box-shadow: {colors["shadow_hover"]};
        }}
        .aizs-entry-card h3 {{
            font-size: 1.5rem;
            font-weight: {typography["font_weight_bold"]};
            margin-bottom: {spacing["spacing_sm"]};
        }}
        .aizs-entry-card p {{
            color: {colors["text_secondary"]};
            margin-bottom: {spacing["spacing_base"]};
            line-height: {typography["line_height_lg"]};
        }}
        .aizs-entry-card ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .aizs-entry-card li {{
            color: {colors["text_secondary"]};
            margin-bottom: {spacing["spacing_xxs"]};
        }}
        .aizs-entry-card li b {{
            color: {colors["text_primary"]};
        }}
        .aizs-feature-section {{
            text-align: center;
            padding: {spacing["spacing_lg"]} 0;
        }}
        .aizs-feature-section h4 {{
            font-size: 1.2rem;
            font-weight: {typography["font_weight_medium"]};
            color: {colors["text_primary"]};
            margin-bottom: {spacing["spacing_base"]};
        }}
        .aizs-feature-tags {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: {spacing["spacing_sm"]};
        }}
        .aizs-feature-tag {{
            background: {colors["bg_hover"]};
            padding: {spacing["spacing_xs"]} {spacing["spacing_base"]};
            border-radius: {radius["radius_round"]};
            color: {colors["text_secondary"]};
            font-size: {typography["font_size_sm"]};
            transition: all {theme["transitions"]["transition_fast"]};
        }}
        .aizs-feature-tag:hover {{
            background: {colors["primary"]};
            color: {colors["primary_text"]};
        }}
        </style>
        ''',
        unsafe_allow_html=True
    )

    # 品牌头部区域
    st.markdown("""
    <div class="aizs-brand-header">
        <h1>🏫 AIZS｜中南财经政法大学 智能咨询平台</h1>
        <p>面向学生、家长与教职工的智能咨询系统</p>
        <div class="aizs-brand-tags">
            <span class="aizs-brand-tag">RAG 检索增强</span>
            <span class="aizs-brand-tag">Agent 多步推理</span>
            <span class="aizs-brand-tag">知识库管理</span>
            <span class="aizs-brand-tag">数据看板</span>
            <span class="aizs-brand-tag">质量评估</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 双栏入口卡片
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("""
        <div class="aizs-entry-card">
            <h3>💬 进入用户端</h3>
            <p>学生和家长可进行校园咨询、查看来源引用、浏览历史对话并提交反馈。</p>
            <ul>
                <li><b>智能校园咨询</b>：支持招生、学务、后勤及生活事务问答</li>
                <li><b>参考来源溯源</b>：提供真实的文档出处和物理页码</li>
                <li><b>Agent 推理演示</b>：执行多步复杂任务拆解，直观展示 <b>Agent 执行轨迹</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        if st.button("👉 进入用户端", key="enter_user_btn", type="primary", use_container_width=True):
            st.session_state.app_mode = "user"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="aizs-entry-card">
            <h3>🛠️ 进入管理端</h3>
            <p>管理员可维护知识库、批量导入资料、查看运营看板、日志和质量评估。</p>
            <ul>
                <li><b>知识库管理与批量导入</b>：支持 ZIP 压缩包及演示包一键注册</li>
                <li><b>可视化 Plotly 看板</b>：呈现问答趋势、意图分布与无来源统计</li>
                <li><b>多维度审计与评估</b>：涵盖日志审计、质量扣分器及自检诊断</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        if st.button("👉 进入管理端", key="enter_admin_btn", type="secondary", use_container_width=True):
            st.session_state.app_mode = "admin"
            st.rerun()

    # 底部功能亮点
    st.markdown("---")
    st.markdown("""
    <div class="aizs-feature-section">
        <h4>✨ 平台功能亮点</h4>
        <div class="aizs-feature-tags">
            <span class="aizs-feature-tag">📖 来源可追溯</span>
            <span class="aizs-feature-tag">💬 支持多轮对话</span>
            <span class="aizs-feature-tag">📦 批量知识库导入</span>
            <span class="aizs-feature-tag">🔧 Agent 工具调用</span>
            <span class="aizs-feature-tag">🎯 低质量回答审计</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 页脚
    render_nav_footer()

# --- 模式二：User 用户咨询端 ---
elif st.session_state.app_mode == "user":
    from page_views import user_chat_view, user_history_view, user_agent_demo_view

    # 渲染用户端定制侧边栏
    st.sidebar.markdown(f"""
    <div style="padding:{spacing['spacing_base']};background:{colors['bg_card']};border-radius:{radius['radius_lg']};margin-bottom:{spacing['spacing_base']};">
        <h2 style="text-align: center; color: {colors['primary']}; font-size:{typography['font_size_lg']}; margin:0;">🏫 AIZS 用户端</h2>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"<h3 style='color:{colors['text_primary']};'>🧭 导航菜单</h3>", unsafe_allow_html=True)

    if st.sidebar.button("💬 智能咨询", key="nav_user_chat", use_container_width=True, type="primary" if st.session_state.user_page == "chat" else "secondary"):
        st.session_state.user_page = "chat"
        st.rerun()

    if st.sidebar.button("⏳ 对话历史", key="nav_user_history", use_container_width=True, type="primary" if st.session_state.user_page == "history" else "secondary"):
        st.session_state.user_page = "history"
        st.rerun()

    if st.sidebar.button("🤖 Agent 智能演示", key="nav_user_agent_demo", use_container_width=True, type="primary" if st.session_state.user_page == "agent_demo" else "secondary"):
        st.session_state.user_page = "agent_demo"
        st.rerun()

    # 底部返回首页按钮
    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 返回系统首页", key="nav_user_home", use_container_width=True):
        st.session_state.app_mode = "home"
        st.rerun()

    # 动态渲染子页面
    if st.session_state.user_page == "chat":
        user_chat_view.render()
    elif st.session_state.user_page == "history":
        user_history_view.render()
    elif st.session_state.user_page == "agent_demo":
        user_agent_demo_view.render()

# --- 模式三：Admin 管理后台 ---
elif st.session_state.app_mode == "admin":
    # 1. 登录校验逻辑
    if not st.session_state.get("admin_logged_in", False):
        # 未登录时隐藏侧边栏导航，只显示返回首页按钮
        st.sidebar.markdown(f"""
        <div style="padding:{spacing['spacing_base']};background:{colors['bg_card']};border-radius:{radius['radius_lg']};margin-bottom:{spacing['spacing_base']};">
            <h2 style="text-align: center; color: {colors['warning']}; font-size:{typography['font_size_lg']}; margin:0;">🛠️ AIZS 管理后台</h2>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown("---")
        if st.sidebar.button("🏠 返回系统首页", key="nav_admin_login_home", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()

        # 登录页面主体
        st.markdown(f"""
        <div style="max-width:400px;margin:0 auto;padding:{spacing['spacing_xxl']} 0;">
            <div style="text-align: center; margin-bottom: {spacing['spacing_lg']};">
                <div style="font-size:4rem;margin-bottom:{spacing['spacing_base']};">🛠️</div>
                <h2 style="color: {colors['text_primary']}; font-weight: {typography['font_weight_bold']}; font-size:1.8rem;">AIZS 管理端登录</h2>
                <p style="color: {colors['text_tertiary']}; font-size: {typography['font_size_base']};">请以管理员身份登录后访问管理后台。</p>
            </div>
            <div style="background:{colors['bg_card']};padding:{spacing['spacing_lg']};border-radius:{radius['radius_lg']};box-shadow:{colors['shadow_card']};">
        """, unsafe_allow_html=True)

        with st.form("admin_login_form"):
            st.markdown(f"<h3 style='color:{colors['text_primary']};margin-bottom:{spacing['spacing_base']};'>🔐 管理员登录</h3>", unsafe_allow_html=True)
            username = st.text_input("用户名", placeholder="请输入管理员用户名")
            password = st.text_input("密码", type="password", placeholder="请输入管理员密码")
            submitted = st.form_submit_button("登录", type="primary", use_container_width=True)

            if submitted:
                expected_user = settings.ADMIN_USERNAME
                expected_pass = settings.ADMIN_PASSWORD

                if not expected_user or not expected_pass:
                    st.error("❌ 系统未配置管理员账户信息，请在 .env 中设置 ADMIN_USERNAME 和 ADMIN_PASSWORD。")
                elif username == expected_user and password == expected_pass:
                    st.session_state["admin_logged_in"] = True
                    st.session_state["admin_username"] = username
                    st.success("✅ 登录成功！正在跳转...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误，请重新输入。")

        st.markdown("</div></div>", unsafe_allow_html=True)

    # 2. 已登录管理后台展示
    else:
        from page_views import (
            admin_knowledge_center_view, admin_dashboard_view,
            admin_session_logs_view, admin_tool_logs_view,
            admin_quality_view, admin_system_check_view
        )

        st.sidebar.markdown(f"""
        <div style="padding:{spacing['spacing_base']};background:{colors['bg_card']};border-radius:{radius['radius_lg']};margin-bottom:{spacing['spacing_base']};">
            <h2 style="text-align: center; color: {colors['warning']}; font-size:{typography['font_size_lg']}; margin:0;">🛠️ AIZS 管理后台</h2>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.markdown("---")

        # 导航菜单
        st.sidebar.markdown(f"<h3 style='color:{colors['text_primary']};'>🧭 导航菜单</h3>", unsafe_allow_html=True)

        if st.sidebar.button("📚 知识库导入与管理", key="nav_admin_knowledge_center", use_container_width=True, type="primary" if st.session_state.admin_page == "knowledge_center" else "secondary"):
            st.session_state.admin_page = "knowledge_center"
            st.rerun()

        if st.sidebar.button("📊 数据看板", key="nav_admin_dashboard", use_container_width=True, type="primary" if st.session_state.admin_page == "dashboard" else "secondary"):
            st.session_state.admin_page = "dashboard"
            st.rerun()

        if st.sidebar.button("📜 会话日志", key="nav_admin_session_logs", use_container_width=True, type="primary" if st.session_state.admin_page == "session_logs" else "secondary"):
            st.session_state.admin_page = "session_logs"
            st.rerun()

        if st.sidebar.button("🔌 工具调用日志", key="nav_admin_tool_logs", use_container_width=True, type="primary" if st.session_state.admin_page == "tool_logs" else "secondary"):
            st.session_state.admin_page = "tool_logs"
            st.rerun()

        if st.sidebar.button("🎯 回答质量评估", key="nav_admin_quality", use_container_width=True, type="primary" if st.session_state.admin_page == "quality" else "secondary"):
            st.session_state.admin_page = "quality"
            st.rerun()

        if st.sidebar.button("🩺 系统自检", key="nav_admin_system_check", use_container_width=True, type="primary" if st.session_state.admin_page == "system_check" else "secondary"):
            st.session_state.admin_page = "system_check"
            st.rerun()

        # 管理员账户及退出/返回按钮
        st.sidebar.markdown("---")
        admin_name = st.session_state.get("admin_username", "管理员")
        st.sidebar.markdown(f"👤 当前登录：**{admin_name}**")

        if st.sidebar.button("🚪 退出登录", key="nav_admin_logout", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["admin_username"] = None
            st.toast("已退出管理员登录。")
            time.sleep(0.4)
            st.rerun()

        if st.sidebar.button("🏠 返回系统首页", key="nav_admin_home", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()

        # 动态渲染子页面
        if st.session_state.admin_page == "knowledge_center":
            admin_knowledge_center_view.render()
        elif st.session_state.admin_page == "dashboard":
            admin_dashboard_view.render()
        elif st.session_state.admin_page == "session_logs":
            admin_session_logs_view.render()
        elif st.session_state.admin_page == "tool_logs":
            admin_tool_logs_view.render()
        elif st.session_state.admin_page == "quality":
            admin_quality_view.render()
        elif st.session_state.admin_page == "system_check":
            admin_system_check_view.render()
