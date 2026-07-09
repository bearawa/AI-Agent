# -*- coding: utf-8 -*-
"""
AIZS｜统一门户控制中心入口
系统统一通过 streamlit run app.py 启动，内部采用状态机控制分流与权限校验。
"""
import streamlit as st
import time
from config import settings
from repositories import sqlite_repository
from utils.logger import logger
from utils.ui_utils import inject_global_css, render_nav_footer

# 1. 启动时执行数据库表初始化，保证第一次运行应用时库表就绪
try:
    sqlite_repository.init_db()
except Exception as e:
    logger.error(f"应用启动初始化 SQLite 数据库失败: {e}")

# 2. 页面全局配置设定 (在 app.py 头部仅调用一次)
st.set_page_config(
    page_title="AIZS｜校园智能咨询平台",
    page_icon="🏫",
    layout="wide"
)

# 3. 注入全局 CSS 样式
inject_global_css()

# 4. 初始化会话状态
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "home"

# --- 模式一：Home 统一门户首页 ---
if st.session_state.app_mode == "home":
    # 注入 CSS 隐藏侧边栏
    st.markdown(
        '''
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        </style>
        ''',
        unsafe_allow_html=True
    )

    # 品牌头部区域
    st.markdown("""
    <div class="aizs-brand-header">
        <h1>🏫 AIZS｜校园智能咨询平台</h1>
        <p>面向学生、家长与校园管理人员的智能咨询系统</p>
        <div class="brand-tags">
            <span class="brand-tag">RAG 检索增强</span>
            <span class="brand-tag">Agent 多步推理</span>
            <span class="brand-tag">知识库管理</span>
            <span class="brand-tag">数据看板</span>
            <span class="brand-tag">质量评估</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 双栏入口卡片
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="aizs-entry-card user-card">
            <h3 style="color: #1e3c72;">💬 进入用户端</h3>
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
        <div class="aizs-entry-card admin-card">
            <h3 style="color: #e67e22;">🛠️ 进入管理端</h3>
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
    st.markdown("##### ✨ 平台功能亮点")
    tags_html = " ".join([
        '<span class="aizs-feature-tag">📖 来源可追溯</span>',
        '<span class="aizs-feature-tag">💬 支持多轮对话</span>',
        '<span class="aizs-feature-tag">📦 批量知识库导入</span>',
        '<span class="aizs-feature-tag">🔧 Agent 工具调用</span>',
        '<span class="aizs-feature-tag">🎯 低质量回答审计</span>',
    ])
    st.markdown(f'<div style="text-align:center; padding: 10px 0;">{tags_html}</div>', unsafe_allow_html=True)

    # 页脚
    render_nav_footer()

# --- 模式二：User 用户咨询端 ---
elif st.session_state.app_mode == "user":
    from page_views import user_chat_view, user_history_view, user_agent_demo_view

    # 渲染用户端定制侧边栏
    st.sidebar.markdown("<h2 style='text-align: center; color: #1e3c72;'>🏫 AIZS 用户端</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # 初始化 Tab 选择
    if "user_tab" not in st.session_state:
        st.session_state.user_tab = "💬 智能咨询"

    user_tab = st.sidebar.radio(
        "🧭 导航菜单",
        ["💬 智能咨询", "⏳ 对话历史", "🤖 Agent 智能演示"],
        index=["💬 智能咨询", "⏳ 对话历史", "🤖 Agent 智能演示"].index(st.session_state.user_tab)
    )
    st.session_state.user_tab = user_tab

    # 底部返回首页按钮
    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 返回系统首页", use_container_width=True):
        st.session_state.app_mode = "home"
        st.rerun()

    # 动态渲染子页面
    if st.session_state.user_tab == "💬 智能咨询":
        user_chat_view.render()
    elif st.session_state.user_tab == "⏳ 对话历史":
        user_history_view.render()
    elif st.session_state.user_tab == "🤖 Agent 智能演示":
        user_agent_demo_view.render()

# --- 模式三：Admin 管理后台 ---
elif st.session_state.app_mode == "admin":
    # 1. 登录校验逻辑
    if not st.session_state.get("admin_logged_in", False):
        # 未登录时隐藏侧边栏导航，只显示返回首页按钮
        st.sidebar.markdown("<h2 style='text-align: center; color: #2c3e50;'>🏫 AIZS 管理后台</h2>", unsafe_allow_html=True)
        st.sidebar.markdown("---")
        if st.sidebar.button("🏠 返回系统首页", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()

        # 登录页面主体
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 1.5rem;">
            <h2 style="color: #2c3e50; font-weight: 800;">🛠️ AIZS 管理端登录</h2>
            <p style="color: #5a6e85; font-size: 0.95rem;">请以管理员身份登录后访问管理后台。</p>
        </div>
        """, unsafe_allow_html=True)

        col_login_l, col_login_mid, col_login_r = st.columns([1, 1.8, 1])
        with col_login_mid:
            with st.form("admin_login_form"):
                st.markdown("### 🔐 管理员登录")
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

    # 2. 已登录管理后台展示
    else:
        from page_views import (
            admin_knowledge_center_view, admin_dashboard_view,
            admin_session_logs_view, admin_tool_logs_view,
            admin_quality_view, admin_system_check_view
        )

        st.sidebar.markdown("<h2 style='text-align: center; color: #e67e22;'>🛠️ AIZS 管理后台</h2>", unsafe_allow_html=True)
        st.sidebar.markdown("---")

        # 初始化 Tab 选择
        if "admin_tab" not in st.session_state:
            st.session_state.admin_tab = "📚 知识库导入与管理"

        admin_tab = st.sidebar.radio(
            "🧭 导航菜单",
            [
                "📚 知识库导入与管理",
                "📊 数据看板",
                "📜 会话日志",
                "🔌 工具调用日志",
                "🎯 回答质量评估",
                "🩺 系统自检"
            ],
            index=[
                "📚 知识库导入与管理",
                "📊 数据看板",
                "📜 会话日志",
                "🔌 工具调用日志",
                "🎯 回答质量评估",
                "🩺 系统自检"
            ].index(st.session_state.admin_tab)
        )
        st.session_state.admin_tab = admin_tab

        # 管理员账户及退出/返回按钮
        st.sidebar.markdown("---")
        admin_name = st.session_state.get("admin_username", "管理员")
        st.sidebar.markdown(f"👤 当前登录：**{admin_name}**")

        if st.sidebar.button("🚪 退出登录", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["admin_username"] = None
            st.toast("已退出管理员登录。")
            time.sleep(0.4)
            st.rerun()

        if st.sidebar.button("🏠 返回系统首页", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()

        # 动态渲染子页面
        if st.session_state.admin_tab == "📚 知识库导入与管理":
            admin_knowledge_center_view.render()
        elif st.session_state.admin_tab == "📊 数据看板":
            admin_dashboard_view.render()
        elif st.session_state.admin_tab == "📜 会话日志":
            admin_session_logs_view.render()
        elif st.session_state.admin_tab == "🔌 工具调用日志":
            admin_tool_logs_view.render()
        elif st.session_state.admin_tab == "🎯 回答质量评估":
            admin_quality_view.render()
        elif st.session_state.admin_tab == "🩺 系统自检":
            admin_system_check_view.render()
