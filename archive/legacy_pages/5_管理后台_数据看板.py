import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.analytics_service import AnalyticsService
from repositories import sqlite_repository
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav
from utils.display_utils import format_percent

# 初始化数据统计服务
@st.cache_resource
def get_analytics_service():
    return AnalyticsService()

analytics_service = get_analytics_service()

# 页面基本配置
st.set_page_config(
    page_title="数据看板 - AIZS 管理后台",
    page_icon="📊",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# 注入 Premium 风格样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #7f8c8d;
        margin-bottom: 25px;
    }
    .metrics-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border: 1px solid #eef2f3;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📊 AIZS 运营数据看板</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">实时统计并展示 AIZS 校园智能咨询系统的整体运行指标、用户提问意图分布、问答频次趋势及低满意度问答日志。</p>', unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：数据看板")
render_logout_button()

# 1. 实时获取数据库指标
metrics = analytics_service.get_summary_metrics()

# 2. 判断是否空状态
if metrics["total_qa_count"] == 0:
    st.markdown("### 📉 核心运行指标")
    # 展示 0 状态指标卡
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("总咨询问答量", "0 次")
    with c2: st.metric("总会话数", "0 个")
    with c3: st.metric("知识库文档数", f"{metrics['total_doc_count']} 篇")
    with c4: st.metric("用户满意度", "暂无反馈")
    
    st.markdown("---")
    st.info("💡 **暂无运营数据，请先前往 [校园咨询] 页面进行一些校园咨询测试以生成统计图表。**")
else:
    # 3. 正常渲染看板
    st.markdown("### 📉 核心运行指标")
    
    # 满意度百分比友好展示
    sat_str = format_percent(metrics["satisfaction_rate"], default="暂无反馈")

    avg_score_str = f"{metrics['average_quality_score']} 分" if metrics["average_quality_score"] is not None else "暂无评估"

    # 第一行指标卡
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("总咨询问答量", f"{metrics['total_qa_count']} 次")
    with c2:
        st.metric("今日问答量", f"{metrics['today_qa_count']} 次")
    with c3:
        st.metric("总会话数", f"{metrics['total_session_count']} 个")
    with c4:
        st.metric("知识库文档数", f"{metrics['total_doc_count']} 篇")
    with c5:
        st.metric("用户平均满意度", sat_str)

    # 第二行指标卡（挑战档新增指标）
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.metric("平均回答质量分", avg_score_str)
    with cc2:
        st.metric("低质量回答数量", f"{metrics['low_quality_count']} 次")
    with cc3:
        st.metric("工具调用总次数", f"{metrics['total_tool_calls']} 次")
    with cc4:
        # 计算低质量率
        if metrics["total_qa_count"] > 0:
            lq_rate_str = format_percent(metrics["low_quality_count"] / metrics["total_qa_count"])
        else:
            lq_rate_str = "0.0%"
        st.metric("低质量回答占比", lq_rate_str)

    st.markdown("---")

    # 4. 图表区
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 📈 最近 30 天每日问答趋势")
        df_trend = analytics_service.get_daily_trend(days=30)
        if not df_trend.empty:
            # 绘制折线图
            fig_trend = px.line(
                df_trend, 
                x="date", 
                y="qa_count", 
                labels={"date": "日期", "qa_count": "问答次数"},
                title="每日咨询问答量变化趋势",
                markers=True,
                color_discrete_sequence=["#4b6cb7"]
            )
            fig_trend.update_layout(hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig_trend.update_xaxes(showgrid=True, gridcolor="#f1f2f6")
            fig_trend.update_yaxes(showgrid=True, gridcolor="#f1f2f6")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("暂无趋势数据")

    with col_chart2:
        st.markdown("#### 🎯 用户提问意图分布")
        df_intent = analytics_service.get_intent_distribution()
        if not df_intent.empty:
            # 绘制饼图
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
            st.warning("暂无意图分布数据（可能均为历史数据且未做意图分类）")

    st.markdown("---")

    # 热门提问与点踩日志
    col_table1, col_table2 = st.columns(2)

    with col_table1:
        st.markdown("#### 🔥 热门提问 Top 10")
        df_top = analytics_service.get_top_questions(limit=10)
        if not df_top.empty:
            # 绘制水平条形图
            fig_top = px.bar(
                df_top.iloc[::-1], # 翻转以便最高频的显示在最上面
                x="count",
                y="question",
                orientation='h',
                labels={"count": "提问频次", "question": "咨询问题"},
                title="提问频次最高的 Top 10 问题",
                color_discrete_sequence=["#182848"]
            )
            # 控制一下文本排版，防止长提问显示不全
            fig_top.update_layout(yaxis={'categoryorder':'trace'}, margin=dict(l=150))
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("暂无提问数据")

    with col_table2:
        st.markdown("#### 👎 低满意度点踩问答日志")
        df_low = analytics_service.get_low_satisfaction_messages()
        if not df_low.empty:
            # 整理为表格展示
            # 为了防止表格文字过长，展示截断，通过 Streamlit dataframe 展示更友好
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

    # 5. 低质量回答与人工优化列表
    st.markdown("---")
    st.markdown("#### ⚠️ 待人工优化低质量问答清单 (新)")
    df_lq = analytics_service.get_low_quality_messages_detail(limit=10)
    if not df_lq.empty:
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

    # 6. 知识库未命中问题统计
    st.markdown("---")
    st.markdown("#### 🔍 知识库未命中问题统计")

    no_source_rate = analytics_service.get_no_source_rate()
    no_source_msgs = analytics_service.get_no_source_messages(limit=20)

    cc_ns1, cc_ns2 = st.columns(2)
    with cc_ns1:
        ns_rate_str = format_percent(no_source_rate / 100 if no_source_rate is not None else None) if no_source_rate is not None else "暂无数据"
        st.metric("无来源回答占比", f"{no_source_rate:.1f}%" if no_source_rate is not None else "暂无数据")
    with cc_ns2:
        st.metric("无来源回答数量", f"{len(no_source_msgs)} 条")

    df_unanswered = analytics_service.get_unanswered_questions_top(limit=10)
    if not df_unanswered.empty:
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
