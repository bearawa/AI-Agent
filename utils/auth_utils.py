# -*- coding: utf-8 -*-
"""
管理员认证工具 —— AIZS 管理后台登录校验。
管理页面在渲染前调用 check_admin_login() 即可拦截未登录访问。
"""
import streamlit as st
from config import settings


def check_admin_login() -> bool:
    """
    检查管理员登录状态。如果未登录，渲染登录表单并阻止页面继续执行。
    返回 True 表示已登录，可以继续渲染页面。
    如果未登录，该函数内部会调用 st.stop() 阻止后续执行。
    """
    if st.session_state.get("admin_logged_in", False):
        return True

    # 未登录，显示登录表单
    render_login_form()
    st.stop()
    return False


def render_login_form():
    """
    渲染管理员登录表单。
    """
    st.markdown("---")
    st.warning("🔒 **请先以管理员身份登录后再访问管理后台。**")

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
                st.success("✅ 登录成功！")
                import time
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 用户名或密码错误，请重新输入。")


def render_logout_button():
    """
    在侧边栏渲染退出登录按钮。
    """
    if st.session_state.get("admin_logged_in", False):
        st.sidebar.markdown("---")
        admin_name = st.session_state.get("admin_username", "管理员")
        st.sidebar.markdown(f"👤 当前登录：**{admin_name}**")
        if st.sidebar.button("🚪 退出登录", use_container_width=True):
            st.session_state["admin_logged_in"] = False
            st.session_state["admin_username"] = None
            st.toast("已退出管理员登录。")
            import time
            time.sleep(0.5)
            st.rerun()


def render_sidebar_nav():
    """
    兼容旧页面调用的侧边栏渲染函数。

    当前项目已统一通过 app.py 内部状态机分流，旧的 Streamlit pages 多页面文件
    已归档到 archive/legacy_pages/。本函数不再生成旧 pages 链接，避免出现
    重复的知识库管理入口。
    """
    # 1. 注入 CSS 隐藏默认的 stSidebarNav 列表
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. 当前主流程由 app.py 管理，这里仅保留兼容提示
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = "home"

    mode = st.session_state["app_mode"]

    # 3. 渲染兼容说明，不再暴露旧多页面入口
    st.sidebar.markdown(f"## 🏫 AIZS｜{'管理后台' if mode == 'admin' else '校园智能咨询'}")
    st.sidebar.markdown("---")
    st.sidebar.info("当前项目统一通过 `streamlit run app.py` 启动，请从首页进入用户端或管理端。")

    if mode == "admin":
        render_logout_button()

    st.sidebar.markdown("---")
