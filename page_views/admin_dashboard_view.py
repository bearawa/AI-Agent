# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 数据看板视图
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from services.analytics_service import AnalyticsService
from utils.display_utils import format_percent, safe_text
from utils.ui_utils import render_page_header, render_empty_state, render_metric_card

@st.cache_resource
def get_analytics_service():
    return AnalyticsService()

def render():
    analytics_service = get_analytics_service()

    render_page_header(
        "📊 AIZS 运营数据看板",
        "实时统计并展示 AIZS 校园智能咨询系统的整体运行指标、用户提问意图分布、问答频次趋势及低满意度问答日志。"
    )

    metrics = analytics_service.get_summary_metrics()

    if not metrics or metrics.get("total_qa_count", 0) == 0:
        # 空数据状态 - 指标卡片展示为0
        st.markdown("### 📉 核心运行指标")
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric_card("总咨询问答量", "0 次")
        with c2: render_metric_card("总会话数", "0 个")
        with c3: render_metric_card("知识库文档数", f"{metrics.get('total_doc_count', 0) if metrics else 0} 篇")
        with c4: render_metric_card("用户满意度", "暂无反馈")

        st.markdown("---")
        render_empty_state(
            title="暂无运营数据",
            description="请先导入知识库并进行咨询测试，以生成统计图表。",
            icon="📊"
        )
    else:
        # 核心运行指标卡片
        st.markdown("### 📉 核心运行指标")

        sat_str = format_percent(metrics["satisfaction_rate"], default="暂无反馈")
        avg_score_val = metrics.get("average_quality_score")
        avg_score_str = f"{avg_score_val:.2f} 分" if avg_score_val is not None else "暂无评估"
        no_source_rate_val = metrics.get("no_source_rate", 0.0) or 0.0

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: render_metric_card("总问答量", f"{metrics.get('total_qa_count', 0)} 次")
        with c2: render_metric_card("今日问答量", f"{metrics.get('today_qa_count', 0)} 次")
        with c3: render_metric_card("会话数", f"{metrics.get('total_session_count', 0)} 个")
        with c4: render_metric_card("文档数", f"{metrics.get('total_doc_count', 0)} 篇")
        with c5: render_metric_card("满意度", sat_str)
        with c6: render_metric_card("无来源率", f"{no_source_rate_val:.1f}%")
        with c7: render_metric_card("平均质量分", avg_score_str)

        st.markdown("---")

        # 图表区域
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("#### 📈 最近 30 天每日问答趋势")
            df_trend = analytics_service.get_daily_trend(days=30)
            if df_trend is not None and not df_trend.empty:
                fig_trend = px.line(
                    df_trend,
                    x="date",
                    y="qa_count",
                    labels={"date": "日期", "qa_count": "问答次数"},
                    title="每日咨询问答量变化趋势",
                    markers=True,
                    color_discrete_sequence=["#1e3c72"]
                )
                fig_trend.update_layout(hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                fig_trend.update_xaxes(showgrid=True, gridcolor="#f1f2f6")
                fig_trend.update_yaxes(showgrid=True, gridcolor="#f1f2f6")
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                render_empty_state(title="暂无趋势数据", description="需要更多问答数据以生成趋势图。", icon="📈")

        with col_chart2:
            st.markdown("#### 🎯 用户提问意图分布")
            df_intent = analytics_service.get_intent_distribution()
            if df_intent is not None and not df_intent.empty:
                fig_intent = px.pie(
                    df_intent,
                    values="count",
                    names="intent_name",
                    title="用户咨询场景意图分布比例",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_intent.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_intent, use_container_width=True)
            else:
                render_empty_state(title="暂无意图分布数据", description="需要更多问答数据以生成意图分布图。", icon="🎯")

        st.markdown("---")

        # 热门问题与低满意度日志
        col_table1, col_table2 = st.columns(2)

        with col_table1:
            st.markdown("#### 🔥 热门提问 Top 10")
            df_top = analytics_service.get_top_questions(limit=10)
            if df_top is not None and not df_top.empty:
                fig_top = px.bar(
                    df_top.iloc[::-1],
                    x="count",
                    y="question",
                    orientation='h',
                    labels={"count": "提问频次", "question": "咨询问题"},
                    title="提问频次最高的 Top 10 问题",
                    color_discrete_sequence=["#1e3c72"]
                )
                fig_top.update_layout(yaxis={'categoryorder':'trace'}, margin=dict(l=150))
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                render_empty_state(title="暂无提问数据", description="用户咨询后将在此展示热门问题排行。", icon="🔥")

        with col_table2:
            st.markdown("#### 👎 低满意度点踩问答日志")
            df_low = analytics_service.get_low_satisfaction_messages()
            if df_low is not None and not df_low.empty:
                st.dataframe(
                    df_low[["feedback_time", "user_question", "assistant_answer", "comment"]].rename(columns={
                        "feedback_time": "时间",
                        "user_question": "用户问题",
                        "assistant_answer": "客服回答",
                        "comment": "用户意见"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("✨ **当前暂无点踩或低满意度反馈，系统表现很棒！**")

        st.markdown("---")

        # 低质量问答清单
        st.markdown("#### ⚠️ 待人工优化低质量问答清单")
        df_lq = analytics_service.get_low_quality_messages_detail(limit=10)
        if df_lq is not None and not df_lq.empty:
            st.dataframe(
                df_lq[["time", "user_question", "assistant_answer", "score", "issues", "suggestion"]].rename(columns={
                    "time": "评估时间",
                    "user_question": "用户问题",
                    "assistant_answer": "助手回复摘要",
                    "score": "评估分",
                    "issues": "缺陷特征",
                    "suggestion": "改进建议"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✨ **当前暂无低质量回答记录，系统质量很高！**")

        st.markdown("---")

        # 未命中问题统计
        st.markdown("#### 🔍 知识库未命中问题统计")

        no_source_rate = analytics_service.get_no_source_rate()
        no_source_msgs = analytics_service.get_no_source_messages(limit=20)

        cc_ns1, cc_ns2 = st.columns(2)
        with cc_ns1:
            ns_rate_val = no_source_rate if no_source_rate is not None else 0.0
            render_metric_card("无来源回答占比", f"{ns_rate_val:.1f}%")
        with cc_ns2:
            ns_count = len(no_source_msgs) if no_source_msgs is not None else 0
            render_metric_card("无来源回答数量", f"{ns_count} 条")

        df_unanswered = analytics_service.get_unanswered_questions_top(limit=10)
        if df_unanswered is not None and not df_unanswered.empty:
            st.markdown("##### 🔥 知识库未命中问题 Top 10")
            st.caption("💡 建议管理员补充相关资料到知识库，提升系统覆盖率。")
            st.dataframe(
                df_unanswered.rename(columns={
                    "question": "用户提问",
                    "count": "出现次数"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✨ **暂无未命中问题，当前知识库覆盖情况较好。**")
