# -*- coding: utf-8 -*-
"""
AIZS 统一前端样式与组件工具集。
视觉规范迁移至 ChatGPT 风格：极简、扁平、无大范围渐变、直角或微圆角、干净的聊天界面。
"""
import streamlit as st

# ── 设计令牌（Design Tokens）──
# ChatGPT 风格的主题色与间距体系
DESIGN_TOKENS = """
:root {
    /* 主色系 */
    --aizs-primary: #10a37f;
    --aizs-primary-light-3: #11b990;
    --aizs-primary-light-5: #11ce9f;
    --aizs-primary-light-7: #a0ebd8;
    --aizs-primary-light-8: #cbf5ea;
    --aizs-primary-light-9: #e6fcf6;
    --aizs-primary-dark-2: #0e906f;

    /* 中性色 */
    --aizs-text-primary: #0d0d0d;
    --aizs-text-regular: #404040;
    --aizs-text-secondary: #5e5e5e;
    --aizs-text-placeholder: #8e8e8e;
    --aizs-border-base: #e5e5e5;
    --aizs-border-light: #ececec;
    --aizs-border-lighter: #f4f4f4;
    --aizs-border-extra-light: #f9f9f9;
    --aizs-bg-page: #ffffff;
    --aizs-bg-overlay: #ffffff;

    /* 功能色 */
    --aizs-success: #10a37f;
    --aizs-warning: #f59e0b;
    --aizs-danger: #ef4444;
    --aizs-info: #3b82f6;

    /* 圆角 */
    --aizs-radius-sm: 4px;
    --aizs-radius-base: 8px;
    --aizs-radius-lg: 12px;
    --aizs-radius-xl: 16px;
    --aizs-radius-pill: 20px;

    /* 阴影 - 更克制 */
    --aizs-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --aizs-shadow-base: 0 2px 4px rgba(0, 0, 0, 0.05);
    --aizs-shadow-hover: 0 4px 6px rgba(0, 0, 0, 0.1);
    --aizs-shadow-primary: 0 2px 4px rgba(16, 163, 127, 0.2);

    /* 过渡 */
    --aizs-transition: all 0.2s ease-in-out;
}

[data-theme="dark"] {
    --aizs-text-primary: #ececec;
    --aizs-text-regular: #b4b4b4;
    --aizs-text-secondary: #8e8e8e;
    --aizs-border-base: #424242;
    --aizs-bg-page: #212121;
    --aizs-bg-overlay: #2f2f2f;
}
"""


def inject_global_css():
    """注入全局 CSS 样式。视觉规范对齐 ChatGPT 极简风格。"""
    st.markdown(f"""
    <style>
    {DESIGN_TOKENS}

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: var(--aizs-border-base);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--aizs-text-secondary); }}

    /* ===== 全局基础 ===== */
    .stApp {{
        font-family: Söhne, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif, Helvetica Neue, Arial, "PingFang SC", "Microsoft YaHei";
        color: var(--aizs-text-primary);
        background-color: var(--aizs-bg-page);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}

    /* ===== Chat 消息样式 - 模拟 ChatGPT ===== */
    /* 用户消息背景 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
        background-color: var(--aizs-bg-page);
        padding: 24px;
    }}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {{
        background-color: var(--aizs-border-lighter);
        padding: 12px 20px;
        border-radius: 24px;
        display: inline-block;
        max-width: 80%;
        margin-left: auto;
    }}

    /* 助手消息背景 */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
        background-color: var(--aizs-bg-page);
        padding: 24px;
    }}
    [data-testid="stChatMessageAvatarAssistant"] {{
        background-color: var(--aizs-primary);
        color: white;
    }}

    /* ===== 卡片 — 扁平化，去除边框 ===== */
    .aizs-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-base);
        padding: 20px;
        box-shadow: var(--aizs-shadow-sm);
        border: 1px solid var(--aizs-border-base);
        margin-bottom: 16px;
        transition: var(--aizs-transition);
    }}

    /* ===== 指标卡片 ===== */
    .aizs-metric-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-base);
        padding: 20px;
        text-align: center;
        border: 1px solid var(--aizs-border-base);
        box-shadow: var(--aizs-shadow-sm);
        margin-bottom: 12px;
    }}
    .aizs-metric-card .metric-value {{
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--aizs-text-primary);
        margin: 0;
        line-height: 1.2;
    }}
    .aizs-metric-card .metric-label {{
        font-size: 0.85rem;
        color: var(--aizs-text-secondary);
        margin-top: 6px;
    }}
    .aizs-metric-card .metric-help {{
        font-size: 0.75rem;
        color: var(--aizs-text-placeholder);
        margin-top: 4px;
    }}

    /* ===== 信息卡片 ===== */
    .aizs-info-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-base);
        padding: 16px;
        border: 1px solid var(--aizs-border-base);
        margin-bottom: 14px;
    }}
    .aizs-info-card h4 {{
        margin: 0 0 8px 0;
        color: var(--aizs-text-primary);
        font-weight: 600;
    }}
    .aizs-info-card p {{
        margin: 0;
        color: var(--aizs-text-regular);
        font-size: 0.9rem;
        line-height: 1.6;
    }}

    /* ===== 空数据状态 ===== */
    .aizs-empty-state {{
        text-align: center;
        padding: 48px 20px;
        margin: 16px 0;
    }}
    .aizs-empty-state .empty-icon {{ font-size: 2.8rem; margin-bottom: 14px; opacity: 0.5; }}
    .aizs-empty-state .empty-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--aizs-text-primary);
        margin-bottom: 6px;
    }}
    .aizs-empty-state .empty-desc {{
        font-size: 0.9rem;
        color: var(--aizs-text-secondary);
    }}

    /* ===== 提示框 ===== */
    .aizs-warning-box, .aizs-success-box, .aizs-error-box {{
        border-radius: var(--aizs-radius-base);
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.9rem;
        border: 1px solid;
    }}
    .aizs-warning-box {{
        background: #fdf6ec;
        border-color: #f3d19e;
        color: #b88230;
    }}
    .aizs-success-box {{
        background: #f0f9eb;
        border-color: #c2e7b0;
        color: #529b2e;
    }}
    .aizs-error-box {{
        background: #fef0f0;
        border-color: #fbc4c4;
        color: #c45656;
    }}

    /* ===== 页面标题区 ===== */
    .aizs-page-header {{
        padding: 20px 0 16px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--aizs-border-base);
    }}
    .aizs-page-header h2 {{
        color: var(--aizs-text-primary);
        font-weight: 700;
        margin: 0 0 6px 0;
    }}
    .aizs-page-header .subtitle {{
        color: var(--aizs-text-secondary);
        font-size: 0.95rem;
        margin: 0;
    }}

    /* ===== 页脚 ===== */
    .aizs-footer {{
        text-align: center;
        padding: 16px 0;
        color: var(--aizs-text-placeholder);
        font-size: 0.8rem;
        border-top: 1px solid var(--aizs-border-base);
        margin-top: 30px;
    }}

    /* ===== 入口卡片 ===== */
    .aizs-entry-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-lg);
        padding: 24px;
        min-height: 260px;
        border: 1px solid var(--aizs-border-base);
        transition: var(--aizs-transition);
        height: 100%;
    }}
    .aizs-entry-card:hover {{
        border-color: var(--aizs-text-placeholder);
    }}
    .aizs-entry-card h3 {{ margin: 0 0 12px 0; font-weight: 600; color: var(--aizs-text-primary); }}
    .aizs-entry-card p {{
        color: var(--aizs-text-regular);
        font-size: 0.95rem;
        line-height: 1.5;
        margin: 0 0 12px 0;
    }}
    .aizs-entry-card ul {{ padding-left: 20px; margin: 0; }}
    .aizs-entry-card ul li {{
        color: var(--aizs-text-regular);
        font-size: 0.9rem;
        line-height: 1.5;
    }}

    /* ===== Streamlit 原生组件覆写 ===== */
    .stButton > button {{
        border-radius: var(--aizs-radius-base) !important;
        font-weight: 500 !important;
        border: 1px solid var(--aizs-border-base) !important;
        background-color: var(--aizs-bg-overlay) !important;
        color: var(--aizs-text-primary) !important;
    }}
    .stButton > button:hover {{
        background-color: var(--aizs-border-lighter) !important;
        border-color: var(--aizs-border-base) !important;
        color: var(--aizs-text-primary) !important;
    }}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        background-color: var(--aizs-primary) !important;
        color: white !important;
        border-color: var(--aizs-primary) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {{
        background-color: var(--aizs-primary-dark-2) !important;
        border-color: var(--aizs-primary-dark-2) !important;
    }}

    /* 输入框圆角 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: var(--aizs-radius-base) !important;
        border-color: var(--aizs-border-base) !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--aizs-primary) !important;
        box-shadow: 0 0 0 1px var(--aizs-primary) !important;
    }}

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {{
        background-color: var(--aizs-border-extra-light);
        border-right: none;
    }}

    /* Expander 圆角 */
    .streamlit-expanderHeader {{
        border-radius: var(--aizs-radius-base) !important;
    }}

    /* Selectbox / Multiselect 圆角 */
    .stSelectbox > div > div {{
        border-radius: var(--aizs-radius-base) !important;
    }}

    /* Metric 组件 */
    [data-testid="stMetric"] {{
        background: var(--aizs-bg-overlay);
        padding: 16px;
        border-radius: var(--aizs-radius-base);
        border: 1px solid var(--aizs-border-base);
        box-shadow: none;
    }}

    /* DataFrame 表头 */
    .stDataFrame table thead th {{
        font-weight: 500 !important;
        color: var(--aizs-text-primary) !important;
        border-bottom: 1px solid var(--aizs-border-base) !important;
    }}

    /* ===== 响应式 ===== */
    @media (max-width: 768px) {{
        .aizs-entry-card {{ min-height: auto; padding: 20px; }}
        .aizs-metric-card .metric-value {{ font-size: 1.4rem; }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_page_header(title, subtitle=None, badge=None):
    """渲染统一风格的页面标题区域。"""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="aizs-page-header">
        <h2>{title}{badge_html}</h2>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, help_text=None):
    """渲染指标卡片组件。"""
    help_html = f'<div class="metric-help">{help_text}</div>' if help_text else ""
    st.markdown(f"""
    <div class="aizs-metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {help_html}
    </div>
    """, unsafe_allow_html=True)


def render_info_card(title, body, icon=None):
    """渲染信息卡片组件。"""
    icon_html = f"{icon} " if icon else ""
    st.markdown(f"""
    <div class="aizs-info-card">
        <h4>{icon_html}{title}</h4>
        <p>{body}</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(title, description, icon="📭"):
    """渲染空数据状态组件。"""
    st.markdown(f"""
    <div class="aizs-empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-title">{title}</div>
        <div class="empty-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_warning_box(message):
    """渲染警告提示框。"""
    st.markdown(f'<div class="aizs-warning-box">⚠️ {message}</div>', unsafe_allow_html=True)


def render_success_box(message):
    """渲染成功提示框。"""
    st.markdown(f'<div class="aizs-success-box">✅ {message}</div>', unsafe_allow_html=True)


def render_error_box(message):
    """渲染错误提示框。"""
    st.markdown(f'<div class="aizs-error-box">❌ {message}</div>', unsafe_allow_html=True)


def render_nav_footer():
    """渲染统一页脚。"""
    st.markdown("""
    <div class="aizs-footer">
        AIZS 中南财经政法大学 智能咨询平台 &copy; 2026 | 基于 RAG + Agent 的智能问答系统
    </div>
    """, unsafe_allow_html=True)
