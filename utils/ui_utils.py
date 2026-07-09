# -*- coding: utf-8 -*-
"""
AIZS 统一前端样式与组件工具集。
所有页面应使用本模块注入全局 CSS 和渲染通用组件，保证视觉风格一致。
"""
import streamlit as st


def inject_global_css():
    """
    注入全局 CSS 样式。统一字体、背景、按钮、卡片、表格、提示框样式。
    必须在每个页面渲染前调用，使用 unsafe_allow_html=True。
    """
    st.markdown("""
    <style>
    /* ===== 全局基础样式 ===== */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                     "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica,
                     Arial, sans-serif;
    }

    /* ===== 主标题隐藏默认 Streamlit 标题间距 ===== */
    [data-testid="stHeader"] {
        background: transparent;
    }

    /* ===== 统一卡片样式 ===== */
    .aizs-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
        border: 1px solid #eef2f7;
        margin-bottom: 16px;
        transition: box-shadow 0.2s ease;
    }
    .aizs-card:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }

    /* ===== 指标卡片 ===== */
    .aizs-metric-card {
        background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        border: 1px solid #e3eaf5;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    .aizs-metric-card .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e3c72;
        margin: 0;
        line-height: 1.2;
    }
    .aizs-metric-card .metric-label {
        font-size: 0.82rem;
        color: #6c757d;
        margin-top: 6px;
    }
    .aizs-metric-card .metric-help {
        font-size: 0.75rem;
        color: #95a5a6;
        margin-top: 4px;
    }

    /* ===== 信息卡片 ===== */
    .aizs-info-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 18px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 14px;
    }
    .aizs-info-card h4 {
        margin: 0 0 8px 0;
        color: #2c3e50;
        font-weight: 700;
    }
    .aizs-info-card p {
        margin: 0;
        color: #5a6e85;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* ===== 空数据状态 ===== */
    .aizs-empty-state {
        text-align: center;
        padding: 40px 20px;
        background: #fafbfc;
        border-radius: 12px;
        border: 1px dashed #d5dbe5;
        margin: 16px 0;
    }
    .aizs-empty-state .empty-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    .aizs-empty-state .empty-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4a5568;
        margin-bottom: 6px;
    }
    .aizs-empty-state .empty-desc {
        font-size: 0.88rem;
        color: #8a94a6;
    }

    /* ===== 提示框样式 ===== */
    .aizs-warning-box {
        background: #fff8e1;
        border-left: 4px solid #f9a825;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        color: #6d4c00;
        font-size: 0.9rem;
    }
    .aizs-success-box {
        background: #e8f5e9;
        border-left: 4px solid #43a047;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        color: #1b5e20;
        font-size: 0.9rem;
    }
    .aizs-error-box {
        background: #ffebee;
        border-left: 4px solid #e53935;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 12px 0;
        color: #b71c1c;
        font-size: 0.9rem;
    }

    /* ===== 来源引用卡片 ===== */
    .aizs-source-box {
        background: #f8faff;
        border-left: 4px solid #2a5298;
        padding: 12px 14px;
        border-radius: 6px;
        margin-bottom: 10px;
        font-size: 0.88rem;
    }
    .aizs-source-box strong {
        color: #1e3c72;
    }
    .aizs-source-box .source-text {
        color: #5a6e85;
        font-size: 0.83rem;
        margin-top: 4px;
    }

    /* ===== 页面标题区 ===== */
    .aizs-page-header {
        padding: 20px 0 16px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid #eef2f7;
    }
    .aizs-page-header h2 {
        color: #1e3c72;
        font-weight: 800;
        margin: 0 0 6px 0;
    }
    .aizs-page-header .subtitle {
        color: #5a6e85;
        font-size: 0.95rem;
        margin: 0;
    }
    .aizs-page-header .badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* ===== 页脚 ===== */
    .aizs-footer {
        text-align: center;
        padding: 16px 0;
        color: #95a5a6;
        font-size: 0.8rem;
        border-top: 1px solid #eef2f7;
        margin-top: 30px;
    }

    /* ===== 入口卡片样式 ===== */
    .aizs-entry-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 28px;
        min-height: 260px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        border: 1px solid #eef2f7;
        transition: all 0.3s ease;
        height: 100%;
    }
    .aizs-entry-card:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    .aizs-entry-card.user-card {
        border-top: 4px solid #1e3c72;
    }
    .aizs-entry-card.admin-card {
        border-top: 4px solid #e67e22;
    }
    .aizs-entry-card h3 {
        margin: 0 0 12px 0;
        font-weight: 700;
    }
    .aizs-entry-card p {
        color: #5a6e85;
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0 0 10px 0;
    }
    .aizs-entry-card ul {
        padding-left: 18px;
        margin: 0;
    }
    .aizs-entry-card ul li {
        color: #666;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    /* ===== 功能亮点标签 ===== */
    .aizs-feature-tag {
        display: inline-block;
        background: #f0f4ff;
        color: #1e3c72;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 4px;
        border: 1px solid #d5e0f5;
    }

    /* ===== 品牌头部 ===== */
    .aizs-brand-header {
        text-align: center;
        padding: 2.5rem 1rem;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(30, 60, 114, 0.2);
    }
    .aizs-brand-header h1 {
        color: white;
        margin: 0 0 8px 0;
        font-weight: 800;
        font-size: 2rem;
    }
    .aizs-brand-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.1rem;
        margin: 0;
    }
    .aizs-brand-header .brand-tags {
        margin-top: 14px;
    }
    .aizs-brand-header .brand-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        color: white;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.78rem;
        margin: 3px;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }

    /* ===== 质量徽章 ===== */
    .aizs-quality-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
    }
    .aizs-quality-badge.high { background-color: #2ecc71; }
    .aizs-quality-badge.low { background-color: #e74c3c; }

    /* ===== 状态标签 ===== */
    .aizs-status-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .aizs-status-tag.success { background-color: #e8f5e9; color: #1b5e20; }
    .aizs-status-tag.fail { background-color: #ffebee; color: #c62828; }
    .aizs-status-tag.warning { background-color: #fff8e1; color: #6d4c00; }
    .aizs-status-tag.info { background-color: #e3f2fd; color: #0d47a1; }

    /* ===== 响应式适配 ===== */
    @media (max-width: 768px) {
        .aizs-brand-header h1 {
            font-size: 1.5rem;
        }
        .aizs-brand-header p {
            font-size: 0.95rem;
        }
        .aizs-entry-card {
            min-height: auto;
            padding: 20px;
        }
        .aizs-metric-card .metric-value {
            font-size: 1.4rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_page_header(title, subtitle=None, badge=None):
    """
    渲染统一风格的页面标题区域。
    """
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="aizs-page-header">
        <h2>{title}{badge_html}</h2>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, help_text=None):
    """
    渲染指标卡片组件。
    """
    help_html = f'<div class="metric-help">{help_text}</div>' if help_text else ""
    st.markdown(f"""
    <div class="aizs-metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {help_html}
    </div>
    """, unsafe_allow_html=True)


def render_info_card(title, body, icon=None):
    """
    渲染信息卡片组件。
    """
    icon_html = f"{icon} " if icon else ""
    st.markdown(f"""
    <div class="aizs-info-card">
        <h4>{icon_html}{title}</h4>
        <p>{body}</p>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(title, description, icon="📭"):
    """
    渲染空数据状态组件。
    """
    st.markdown(f"""
    <div class="aizs-empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-title">{title}</div>
        <div class="empty-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def render_warning_box(message):
    """
    渲染警告提示框。
    """
    st.markdown(f"""
    <div class="aizs-warning-box">⚠️ {message}</div>
    """, unsafe_allow_html=True)


def render_success_box(message):
    """
    渲染成功提示框。
    """
    st.markdown(f"""
    <div class="aizs-success-box">✅ {message}</div>
    """, unsafe_allow_html=True)


def render_error_box(message):
    """
    渲染错误提示框。
    """
    st.markdown(f"""
    <div class="aizs-error-box">❌ {message}</div>
    """, unsafe_allow_html=True)


def render_nav_footer():
    """
    渲染统一页脚。
    """
    st.markdown("""
    <div class="aizs-footer">
        AIZS 校园智能咨询平台 &copy; 2025 | 基于 RAG + Agent 的智能问答系统
    </div>
    """, unsafe_allow_html=True)
