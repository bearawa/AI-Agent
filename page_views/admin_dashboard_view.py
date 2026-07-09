# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 运营数据仪表盘
重构版：使用主题管理器和组件库提供企业级用户体验。
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services.analytics_service import AnalyticsService
from utils.ui_utils import render_page_header, render_empty_state
from themes.theme_manager import theme_manager

theme = theme_manager.current_theme
colors = theme["colors"]
spacing = theme["spacing"]
typography = theme["typography"]
radius = theme["radius"]


@st.cache_resource
def get_analytics_service():
    return AnalyticsService()


def _render_metric_card(label, value, delta=None, delta_color="normal"):
    """渲染自定义指标卡片。"""
    delta_html = ""
    if delta is not None:
        delta_style = "color:#2ecc71" if delta_color == "normal" else "color:#e74c3c"
        delta_html = f'<div style="{delta_style};font-size:{typography["font_size_sm"]};margin-top:{spacing["spacing_xxs"]};">{delta}</div>'
    
    st.markdown(f"""
    <div style="background:{colors['bg_card']};border-radius:{radius['radius_lg']};padding:{spacing['spacing_base']};
                box-shadow:{colors['shadow_card']};text-align:center;">
        <div style="font-size:{typography['font_size_xs']};color:{colors['text_tertiary']};text-transform:uppercase;letter-spacing:0.5px;">{label}</div>
        <div style="font-size:2rem;font-weight:{typography['font_weight_bold']};color:{colors['text_primary']};margin-top:{spacing['spacing_xxs']};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render():
    analytics_service = get_analytics_service()

    render_page_header(
        "📊 AIZS 运营数据仪表盘",
        "实时监控系统运行状态、对话量、知识库命中率及回答质量趋势，帮助管理员及时发现问题并优化系统。"
    )

    # ── 核心指标卡片 ──
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📈 核心指标概览</h3>", unsafe_allow_html=True)
    metrics = analytics_service.get_dashboard_metrics()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6, gap="small")
    with col1: _render_metric_card("总对话数", f"{metrics['total_conversations']}")
    with col2: _render_metric_card("今日对话", f"{metrics['today_conversations']}", f"+{metrics['today_conversations']}")
    with col3: _render_metric_card("知识库命中率", f"{metrics['knowledge_hit_rate']:.1f}%")
    with col4: _render_metric_card("平均响应时间", f"{metrics['avg_response_time_ms']}ms")
    with col5: _render_metric_card("好评率", f"{metrics['positive_rating_rate']:.1f}%")
    with col6: _render_metric_card("低质量回答", f"{metrics['low_quality_count']}")

    # ── 趋势图表区域 ──
    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📉 趋势分析</h3>", unsafe_allow_html=True)
    
    time_range_options = ["7天", "30天", "90天"]
    selected_range = st.selectbox("时间范围", time_range_options, index=0, key="dash_time_range")
    days_map = {"7天": 7, "30天": 30, "90天": 90}
    days = days_map[selected_range]

    trend_data = analytics_service.get_trend_data(days=days)

    if not trend_data:
        render_empty_state(
            title="暂无趋势数据",
            description="系统运行一段时间后将自动生成趋势数据。",
            icon="📈"
        )
    else:
        df = pd.DataFrame(trend_data)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "对话量趋势",
                "知识库命中率",
                "平均响应时间",
                "好评率趋势"
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["conversation_count"],
                name="对话量",
                marker_color=colors["primary"],
                opacity=0.8
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Line(
                x=df["date"],
                y=df["knowledge_hit_rate"],
                name="命中率",
                line=dict(color=colors["success"], width=3),
                yaxis="y2"
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Line(
                x=df["date"],
                y=df["avg_response_time_ms"],
                name="响应时间",
                line=dict(color=colors["warning"], width=3)
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Line(
                x=df["date"],
                y=df["positive_rating_rate"],
                name="好评率",
                line=dict(color=colors["info"], width=3)
            ),
            row=2, col=2
        )

        fig.update_layout(
            height=600,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=colors["text_secondary"])
        )

        fig.update_xaxes(
            gridcolor=colors["border"],
            title_font=dict(color=colors["text_tertiary"])
        )
        
        fig.update_yaxes(
            gridcolor=colors["border"],
            title_font=dict(color=colors["text_tertiary"])
        )

        st.plotly_chart(fig, use_container_width=True)

    # ── 意图分布 ──
    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🎯 意图分布</h3>", unsafe_allow_html=True)
    
    intent_dist = analytics_service.get_intent_distribution()
    
    if not intent_dist:
        st.info("暂无意图数据")
    else:
        labels = [item["intent_name"] for item in intent_dist]
        values = [item["count"] for item in intent_dist]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker=dict(colors=[colors["primary"], colors["success"], colors["warning"], colors["error"], colors["info"]]),
            textinfo='label+percent',
            textfont=dict(color=colors["text_secondary"])
        )])
        
        fig.update_layout(
            height=350,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=colors["text_secondary"])
        )
        
        col_pie, col_list = st.columns([1, 1], gap="small")
        with col_pie:
            st.plotly_chart(fig, use_container_width=True)
        with col_list:
            st.markdown(f"<h4 style='color:{colors['text_secondary']};'>意图明细</h4>", unsafe_allow_html=True)
            for item in intent_dist:
                st.markdown(f"- **{item['intent_name']}**: {item['count']} 次 ({item['percentage']:.1f}%)")

    # ── 低质量问答列表 ──
    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>⚠️ 近期低质量问答</h3>", unsafe_allow_html=True)
    
    low_quality_items = analytics_service.get_recent_low_quality(count=5)
    
    if not low_quality_items:
        st.success("近期没有低质量问答记录，回答质量良好！")
    else:
        for item in low_quality_items:
            with st.expander(f"⏱️ {item['time']} | 评分: {item['score']}分 | {item['user_question'][:30]}..."):
                st.markdown(f"""
                <div style="background:{colors['error']}10;border-radius:{radius['radius_base']};padding:{spacing['spacing_base']};margin-bottom:{spacing['spacing_sm']};">
                    <strong>❓ 用户提问：</strong><br/>
                    <span style="color:{colors['text_secondary']};">{item['user_question']}</span>
                </div>
                <div style="background:{colors['warning']}10;border-radius:{radius['radius_base']};padding:{spacing['spacing_base']};margin-bottom:{spacing['spacing_sm']};">
                    <strong>🤖 助手回答：</strong><br/>
                    <span style="color:{colors['text_secondary']};">{item['assistant_answer']}</span>
                </div>
                <div style="background:{colors['bg_card']};border-radius:{radius['radius_base']};padding:{spacing['spacing_base']};">
                    <strong>💡 改进建议：</strong><br/>
                    <span style="color:{colors['text_secondary']};">{item['suggestion']}</span>
                </div>
                """, unsafe_allow_html=True)
