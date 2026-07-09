# -*- coding: utf-8 -*-
"""
AIZS 统一前端样式与组件工具集。
视觉规范迁移自 KOI-UI：圆角卡片、柔和阴影、CSS 变量、悬停动效、细滚动条。
"""
import streamlit as st

# ── 设计令牌（Design Tokens）──
# 迁移自 koi-ui 的主题色与间距体系，适配 Streamlit CSS 注入
DESIGN_TOKENS = """
:root {
    /* 主色系 — 与 koi-ui --el-color-primary 对齐 */
    --aizs-primary: #409EFF;
    --aizs-primary-light-3: #79bbff;
    --aizs-primary-light-5: #a0cfff;
    --aizs-primary-light-7: #c6e2ff;
    --aizs-primary-light-8: #d9ecff;
    --aizs-primary-light-9: #ecf5ff;
    --aizs-primary-dark-2: #337ecc;

    /* 中性色 — koi-ui 文字/边框/背景体系 */
    --aizs-text-primary: #303133;
    --aizs-text-regular: #606266;
    --aizs-text-secondary: #909399;
    --aizs-text-placeholder: #a8abb2;
    --aizs-border-base: #dcdfe6;
    --aizs-border-light: #e4e7ed;
    --aizs-border-lighter: #ebeef5;
    --aizs-border-extra-light: #f2f6fc;
    --aizs-bg-page: #f5f7fa;
    --aizs-bg-overlay: #ffffff;

    /* 功能色 */
    --aizs-success: #67c23a;
    --aizs-warning: #e6a23c;
    --aizs-danger: #f56c6c;
    --aizs-info: #909399;

    /* 圆角 */
    --aizs-radius-sm: 6px;
    --aizs-radius-base: 10px;
    --aizs-radius-lg: 14px;
    --aizs-radius-xl: 18px;
    --aizs-radius-pill: 20px;

    /* 阴影 */
    --aizs-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
    --aizs-shadow-base: 0 4px 16px rgba(0, 0, 0, 0.06);
    --aizs-shadow-hover: 0 8px 30px rgba(0, 0, 0, 0.1);
    --aizs-shadow-primary: 0 4px 14px rgba(64, 158, 255, 0.25);

    /* 过渡 */
    --aizs-transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
}
"""


def inject_global_css():
    """注入全局 CSS 样式。视觉规范完全对齐 KOI-UI。"""
    st.markdown(f"""
    <style>
    {DESIGN_TOKENS}

    /* ===== 滚动条 — koi-ui 6px 细滚动条 ===== */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: var(--aizs-border-base);
        border-radius: 6px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: #b6b6b6; }}

    /* ===== 全局基础 ===== */
    .stApp {{
        font-family: Inter, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                     "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: var(--aizs-text-primary);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}

    /* ===== 卡片 — koi-ui 白底圆角柔阴影 ===== */
    .aizs-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-base);
        padding: 20px;
        box-shadow: var(--aizs-shadow-sm);
        border: 1px solid var(--aizs-border-lighter);
        margin-bottom: 16px;
        transition: var(--aizs-transition);
    }}
    .aizs-card:hover {{
        box-shadow: var(--aizs-shadow-hover);
        transform: translateY(-2px);
    }}

    /* ===== 指标卡片 ===== */
    .aizs-metric-card {{
        background: linear-gradient(135deg, var(--aizs-primary-light-9) 0%, var(--aizs-primary-light-8) 100%);
        border-radius: var(--aizs-radius-base);
        padding: 20px;
        text-align: center;
        border: 1px solid var(--aizs-primary-light-7);
        box-shadow: var(--aizs-shadow-sm);
        margin-bottom: 12px;
        transition: var(--aizs-transition);
    }}
    .aizs-metric-card:hover {{
        box-shadow: var(--aizs-shadow-primary);
        transform: translateY(-2px);
    }}
    .aizs-metric-card .metric-value {{
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--aizs-primary);
        margin: 0;
        line-height: 1.2;
    }}
    .aizs-metric-card .metric-label {{
        font-size: 0.82rem;
        color: var(--aizs-text-secondary);
        margin-top: 6px;
    }}
    .aizs-metric-card .metric-help {{
        font-size: 0.75rem;
        color: var(--aizs-text-placeholder);
        margin-top: 4px;
    }}

    /* ===== 信息卡片 — koi-ui 左边框卡片 ===== */
    .aizs-info-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-base);
        padding: 18px;
        border-left: 4px solid var(--aizs-primary);
        box-shadow: var(--aizs-shadow-sm);
        margin-bottom: 14px;
        transition: var(--aizs-transition);
    }}
    .aizs-info-card:hover {{ box-shadow: var(--aizs-shadow-base); }}
    .aizs-info-card h4 {{
        margin: 0 0 8px 0;
        color: var(--aizs-text-primary);
        font-weight: 700;
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
        background: var(--aizs-bg-page);
        border-radius: var(--aizs-radius-lg);
        border: 1px dashed var(--aizs-border-light);
        margin: 16px 0;
    }}
    .aizs-empty-state .empty-icon {{ font-size: 2.8rem; margin-bottom: 14px; }}
    .aizs-empty-state .empty-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--aizs-text-primary);
        margin-bottom: 6px;
    }}
    .aizs-empty-state .empty-desc {{
        font-size: 0.88rem;
        color: var(--aizs-text-secondary);
    }}

    /* ===== 提示框 — koi-ui 功能色边框卡片 ===== */
    .aizs-warning-box {{
        background: #fdf6ec;
        border-left: 4px solid var(--aizs-warning);
        border-radius: var(--aizs-radius-sm);
        padding: 14px 18px;
        margin: 12px 0;
        color: #b88230;
        font-size: 0.9rem;
    }}
    .aizs-success-box {{
        background: #f0f9eb;
        border-left: 4px solid var(--aizs-success);
        border-radius: var(--aizs-radius-sm);
        padding: 14px 18px;
        margin: 12px 0;
        color: #529b2e;
        font-size: 0.9rem;
    }}
    .aizs-error-box {{
        background: #fef0f0;
        border-left: 4px solid var(--aizs-danger);
        border-radius: var(--aizs-radius-sm);
        padding: 14px 18px;
        margin: 12px 0;
        color: #c45656;
        font-size: 0.9rem;
    }}

    /* ===== 来源引用卡片 ===== */
    .aizs-source-box {{
        background: var(--aizs-primary-light-9);
        border-left: 4px solid var(--aizs-primary);
        padding: 12px 14px;
        border-radius: var(--aizs-radius-sm);
        margin-bottom: 10px;
        font-size: 0.88rem;
    }}
    .aizs-source-box strong {{ color: var(--aizs-primary-dark-2); }}
    .aizs-source-box .source-text {{
        color: var(--aizs-text-regular);
        font-size: 0.83rem;
        margin-top: 4px;
    }}

    /* ===== 页面标题区 ===== */
    .aizs-page-header {{
        padding: 20px 0 16px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--aizs-border-lighter);
    }}
    .aizs-page-header h2 {{
        color: var(--aizs-text-primary);
        font-weight: 800;
        margin: 0 0 6px 0;
    }}
    .aizs-page-header .subtitle {{
        color: var(--aizs-text-regular);
        font-size: 0.95rem;
        margin: 0;
    }}
    .aizs-page-header .badge {{
        display: inline-block;
        background: var(--aizs-primary);
        color: white;
        padding: 3px 10px;
        border-radius: var(--aizs-radius-pill);
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }}

    /* ===== 页脚 ===== */
    .aizs-footer {{
        text-align: center;
        padding: 16px 0;
        color: var(--aizs-text-placeholder);
        font-size: 0.8rem;
        border-top: 1px solid var(--aizs-border-lighter);
        margin-top: 30px;
    }}

    /* ===== 入口卡片 — koi-ui 悬停提升动效 ===== */
    .aizs-entry-card {{
        background: var(--aizs-bg-overlay);
        border-radius: var(--aizs-radius-xl);
        padding: 28px;
        min-height: 260px;
        box-shadow: var(--aizs-shadow-base);
        border: 1px solid var(--aizs-border-lighter);
        transition: var(--aizs-transition);
        height: 100%;
    }}
    .aizs-entry-card:hover {{
        box-shadow: var(--aizs-shadow-hover);
        transform: translateY(-4px);
    }}
    .aizs-entry-card.user-card {{ border-top: 4px solid var(--aizs-primary); }}
    .aizs-entry-card.admin-card {{ border-top: 4px solid var(--aizs-warning); }}
    .aizs-entry-card h3 {{ margin: 0 0 12px 0; font-weight: 700; color: var(--aizs-text-primary); }}
    .aizs-entry-card p {{
        color: var(--aizs-text-regular);
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0 0 10px 0;
    }}
    .aizs-entry-card ul {{ padding-left: 18px; margin: 0; }}
    .aizs-entry-card ul li {{
        color: var(--aizs-text-regular);
        font-size: 0.85rem;
        line-height: 1.6;
    }}

    /* ===== 功能标签 — koi-ui 胶囊标签 ===== */
    .aizs-feature-tag {{
        display: inline-block;
        background: rgba(64, 158, 255, 0.08);
        color: var(--aizs-primary);
        padding: 6px 14px;
        border-radius: var(--aizs-radius-pill);
        font-size: 0.82rem;
        font-weight: 500;
        margin: 4px;
        border: 1px solid rgba(64, 158, 255, 0.15);
        transition: var(--aizs-transition);
    }}
    .aizs-feature-tag:hover {{
        background: rgba(64, 158, 255, 0.15);
        transform: translateY(-2px);
    }}

    /* ===== 品牌头部 — koi-ui 渐变 + 柔阴影 ===== */
    .aizs-brand-header {{
        text-align: center;
        padding: 2.8rem 1rem;
        background: linear-gradient(135deg, var(--aizs-primary) 0%, var(--aizs-primary-dark-2) 100%);
        border-radius: var(--aizs-radius-xl);
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(64, 158, 255, 0.25);
    }}
    .aizs-brand-header h1 {{
        color: white;
        margin: 0 0 8px 0;
        font-weight: 800;
        font-size: 2rem;
    }}
    .aizs-brand-header p {{
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.1rem;
        margin: 0;
    }}
    .aizs-brand-header .brand-tags {{ margin-top: 14px; }}
    .aizs-brand-header .brand-tag {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        color: white;
        padding: 4px 12px;
        border-radius: var(--aizs-radius-pill);
        font-size: 0.78rem;
        margin: 3px;
        border: 1px solid rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(8px);
    }}

    /* ===== 质量徽章 ===== */
    .aizs-quality-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: var(--aizs-radius-pill);
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
    }}
    .aizs-quality-badge.high {{ background-color: var(--aizs-success); }}
    .aizs-quality-badge.low {{ background-color: var(--aizs-danger); }}

    /* ===== 状态标签 ===== */
    .aizs-status-tag {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: var(--aizs-radius-sm);
        font-size: 0.75rem;
        font-weight: bold;
    }}
    .aizs-status-tag.success {{ background: #f0f9eb; color: #529b2e; }}
    .aizs-status-tag.fail {{ background: #fef0f0; color: #c45656; }}
    .aizs-status-tag.warning {{ background: #fdf6ec; color: #b88230; }}
    .aizs-status-tag.info {{ background: #ecf5ff; color: #409eff; }}

    /* ===== Streamlit 原生组件覆写 — koi-ui 风格 ===== */
    .stButton > button {{
        border-radius: var(--aizs-radius-base) !important;
        font-weight: 600 !important;
        transition: var(--aizs-transition) !important;
        border: 1px solid var(--aizs-border-base) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: var(--aizs-shadow-base) !important;
    }}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        box-shadow: var(--aizs-shadow-primary) !important;
    }}

    /* 输入框圆角 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: var(--aizs-radius-base) !important;
    }}

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {{
        background: var(--aizs-bg-page);
        border-right: 1px solid var(--aizs-border-lighter);
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
        border: 1px solid var(--aizs-border-lighter);
        box-shadow: var(--aizs-shadow-sm);
    }}

    /* DataFrame 表头 */
    .stDataFrame table thead th {{
        font-weight: 600 !important;
        color: var(--aizs-text-primary) !important;
    }}

    /* ===== 响应式 ===== */
    @media (max-width: 768px) {{
        .aizs-brand-header h1 {{ font-size: 1.5rem; }}
        .aizs-brand-header p {{ font-size: 0.95rem; }}
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
