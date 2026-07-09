# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 回答质量评估视图
"""
import streamlit as st
import json
from repositories import sqlite_repository
from utils.display_utils import safe_text
from utils.ui_utils import render_page_header, render_empty_state, render_metric_card

def render():
    # 自定义样式
    st.markdown("""
    <style>
        .quality-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
        }
        .badge-high { background-color: #2ecc71; }
        .badge-low { background-color: #e74c3c; }
        .badge-rules { background-color: #3498db; }
        .badge-llm { background-color: #9b59b6; }
    </style>
    """, unsafe_allow_html=True)

    render_page_header(
        "⭐ 回答质量审计与优化",
        "系统管理员可在此页面集中审计客服系统的每一次回答质量，查看评分、分析低质量问答的缺陷，并提取优化建议。"
    )

    # --- 筛选面板 ---
    st.markdown("### 🔍 筛选条件")
    with st.container():
        c1, c2, c3 = st.columns(3)

        with c1:
            quality_filter = st.selectbox("质量类别筛选：", ["全部", "仅低质量回答", "仅高质量回答"])
        with c2:
            score_range = st.slider("质量分数过滤区间：", 1, 5, (1, 5))
        with c3:
            limit_val = st.slider("最大载入条数：", 10, 200, 50)

    # 计算筛选参数
    is_low_quality_val = None
    if quality_filter == "仅低质量回答":
        is_low_quality_val = 1
    elif quality_filter == "仅高质量回答":
        is_low_quality_val = 0

    min_s, max_s = score_range

    evals = sqlite_repository.list_quality_evaluations(
        limit=limit_val,
        is_low_quality=is_low_quality_val,
        min_score=min_s,
        max_score=max_s
    )

    st.markdown("---")
    st.markdown(f"### 📋 质量分析列表 (共 {len(evals)} 条记录)")

    if not evals:
        render_empty_state(
            title="暂无质量评估记录",
            description="没有找到符合当前过滤条件的质量评估记录。请先进行用户咨询以生成评估数据。",
            icon="⭐"
        )
    else:
        for idx, ev in enumerate(evals):
            sess_id = ev["session_id"]
            msg_id = ev["message_id"]
            score = ev["score"]
            is_low = ev["is_low_quality"]
            issues_str = ev["issues"] or "[]"
            suggestion = safe_text(ev["suggestion"], "无建议")
            evaluator = ev["evaluator"]
            created = safe_text(ev["created_at"], "暂无")

            user_q = safe_text(ev["user_question"], "（未知提问）")
            ast_a = safe_text(ev["assistant_answer"], "（无回答内容）")
            intent_cn = safe_text(ev["intent_name"], "其他")

            rating = ev["feedback_rating"]
            comment = ev["feedback_comment"]

            try:
                issues_list = json.loads(issues_str)
            except (json.JSONDecodeError, TypeError):
                issues_list = []

            badge_q = '<span class="quality-badge badge-low">⚠️ 低质量</span>' if is_low == 1 else '<span class="quality-badge badge-high">✅ 高质量</span>'
            if evaluator == "llm":
                badge_ev = '<span class="quality-badge badge-llm">LLM模型评估</span>'
            elif evaluator == "rules_feedback":
                badge_ev = '<span class="quality-badge badge-rules">反馈自动重评估</span>'
            else:
                badge_ev = '<span class="quality-badge badge-rules">规则指标评估</span>'

            feedback_str = "无反馈"
            if rating == "like":
                feedback_str = "👍 赞"
            elif rating == "dislike":
                feedback_str = f"👎 踩 ({safe_text(comment, '无理由')})"

            low_prefix = "⚠️ [低质量] " if is_low == 1 else ""
            card_title = f"{low_prefix}⏱️ {created} | 评分：{score} 分 | 提问：{user_q[:25]}"
            if len(user_q) > 25:
                card_title += "..."

            with st.expander(card_title):
                st.markdown(f"**关联会话 ID:** `{sess_id}` | **关联消息 ID:** `{msg_id}`")
                st.markdown(f"**质量指标:** {badge_q} | **评估方法:** {badge_ev} | **用户反馈:** `{feedback_str}`", unsafe_allow_html=True)
                st.markdown("---")

                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown(f"**❓ 学生提问 (分类: {intent_cn})：**")
                    st.info(user_q)

                    # 缺陷和建议使用折叠区域
                    with st.expander("🔍 缺陷与改进建议"):
                        st.markdown("**识别缺陷：**")
                        if issues_list:
                            for issue in issues_list:
                                st.markdown(f"- ❌ {issue}")
                        else:
                            st.markdown("- ✨ 未检测到明显质量缺陷")

                        st.markdown("**💡 改进建议：**")
                        if is_low == 1:
                            st.warning(suggestion)
                        else:
                            st.success(suggestion)

                with c_right:
                    st.markdown("**🤖 助手回答：**")
                    st.success(ast_a)
