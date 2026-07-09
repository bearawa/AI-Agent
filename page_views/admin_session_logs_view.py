# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 会话日志视图
重构版：使用主题管理器和组件库提供企业级用户体验。
"""
import datetime
import streamlit as st
from services.analytics_service import AnalyticsService
from repositories import sqlite_repository
from utils.display_utils import format_confidence, format_ms, safe_text
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


def render():
    analytics_service = get_analytics_service()

    render_page_header(
        "📜 会话审计日志",
        "系统管理员可在此页面检索、审计全部历史咨询对话，深入还原每次问答的匹配耗时、改写细节及知识库切片引用证据。"
    )

    # ── 筛选控制面板 ──
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🔍 筛选条件</h3>", unsafe_allow_html=True)
    with st.container():
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            today = datetime.date.today()
            seven_days_ago = today - datetime.timedelta(days=7)
            date_range = st.date_input("选择日期范围：", [seven_days_ago, today])
            start_date = None
            end_date = None
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date = date_range[0].strftime("%Y-%m-%d")
                end_date = date_range[1].strftime("%Y-%m-%d")
            elif isinstance(date_range, list) and len(date_range) == 2:
                start_date = date_range[0].strftime("%Y-%m-%d")
                end_date = date_range[1].strftime("%Y-%m-%d")

        with c2:
            intent_mapping = {
                "全部": None,
                "招生": "admission",
                "学务": "academic",
                "后勤": "logistics",
                "校园生活": "campus_life",
                "其他": "other"
            }
            selected_intent_cn = st.selectbox("意图类别筛选：", list(intent_mapping.keys()))
            selected_intent_en = intent_mapping[selected_intent_cn]

        with c3:
            source_options = {
                "全部": None,
                "有参考来源": 1,
                "无参考来源": 0
            }
            selected_source_cn = st.selectbox("包含参考来源：", list(source_options.keys()))
            selected_source_val = source_options[selected_source_cn]

        with c4:
            is_disliked = st.checkbox("🔍 只看点踩(dislike)反馈")
            search_keyword = st.text_input("关键字检索(提问/回答)：", placeholder="请输入搜索词...")

    # 执行数据检索
    logs = analytics_service.get_session_logs(
        start_date=start_date,
        end_date=end_date,
        intent=selected_intent_en,
        has_source=selected_source_val,
        is_disliked=is_disliked,
        search_keyword=search_keyword
    )

    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📋 查询结果 (共 {len(logs)} 条记录)</h3>", unsafe_allow_html=True)

    if not logs:
        render_empty_state(
            title="暂无符合条件的会话日志",
            description="请尝试调整筛选条件或先进行用户咨询测试以生成日志数据。",
            icon="📜"
        )
    else:
        for idx, log in enumerate(logs):
            msg_id = log["message_id"]
            session_id = log["session_id"]
            time_str = safe_text(log["time"], "暂无")
            user_question = safe_text(log["user_question"], "（未知提问）")
            assistant_answer = safe_text(log["assistant_answer"], "（无回答内容）")
            intent_name = log.get("intent_name")
            confidence = log.get("intent_confidence")
            rewritten = log.get("rewritten_query")
            has_src = log.get("has_source")
            time_ms = log.get("response_time_ms")
            rating = log.get("feedback_rating")
            comment = log.get("feedback_comment")

            intent_name_text = safe_text(intent_name, "未识别")
            confidence_text = format_confidence(confidence)

            if has_src == 1:
                source_text = "有来源"
                source_color = colors["success"]
            else:
                source_text = "无来源"
                source_color = colors["error"]

            time_ms_text = format_ms(time_ms)

            rating_str = "无反馈"
            if rating == "like":
                rating_str = "👍 赞"
            elif rating == "dislike":
                rating_str = f"👎 踩 ({safe_text(comment, '未填意见')})"

            summary_title = f"⏱️ {time_str} | 问：{user_question[:25]}"
            if len(user_question) > 25:
                summary_title += "..."

            with st.expander(summary_title):
                st.markdown(f"""
                <div style="display:flex;flex-wrap:wrap;gap:{spacing['spacing_sm']};margin-bottom:{spacing['spacing_base']};">
                    <span style="background:{colors['primary']}15;color:{colors['primary']};padding:4px 10px;border-radius:{radius['radius_base']};font-size:{typography['font_size_xs']};font-weight:{typography['font_weight_bold']};">🎯 意图：{intent_name_text} ({confidence_text} 置信度)</span>
                    <span style="background:{source_color}15;color:{source_color};padding:4px 10px;border-radius:{radius['radius_base']};font-size:{typography['font_size_xs']};font-weight:{typography['font_weight_bold']};">📁 匹配引用：{source_text}</span>
                    <span style="background:{colors['bg_card']};color:{colors['text_secondary']};padding:4px 10px;border-radius:{radius['radius_base']};font-size:{typography['font_size_xs']};font-weight:{typography['font_weight_bold']};border:1px solid {colors['border']};">⚡ 耗时：{time_ms_text}</span>
                    <span style="background:{colors['bg_card']};color:{colors['text_secondary']};padding:4px 10px;border-radius:{radius['radius_base']};font-size:{typography['font_size_xs']};font-weight:{typography['font_weight_bold']};border:1px solid {colors['border']};">💬 反馈：{rating_str}</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**会话 ID:** `{session_id}`")
                st.markdown("---")

                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("**❓ 学生提问：**")
                    st.info(user_question)

                    if rewritten and rewritten != user_question:
                        st.markdown("**🔍 检索改写词：**")
                        st.code(rewritten, language="text")

                with c_right:
                    st.markdown("**🤖 助手回答：**")
                    st.success(assistant_answer)

                if has_src:
                    st.markdown("**📖 引用的知识库来源切片明细：**")
                    sources = sqlite_repository.get_message_sources(msg_id)
                    if not sources:
                        st.caption("数据库中暂无该消息的来源切片索引记录。")
                    else:
                        for src_idx, src in enumerate(sources, 1):
                            page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                            st.markdown(f"""
                            <div style="background:{colors['bg_card']};padding:{spacing['spacing_sm']};border-radius:{radius['radius_base']};border-left:4px solid {colors['primary']};margin-bottom:{spacing['spacing_sm']};border:1px solid {colors['border']};">
                                <strong style="color:{colors['text_primary']};">[{src_idx}] {src['file_name']} ({page_str}) | 相似度匹配值：{(1-src['similarity_distance'])*100:.1f}%</strong>
                                <p style="font-size:{typography['font_size_sm']};color:{colors['text_tertiary']};margin:{spacing['spacing_xxs']} 0 0 0;">{src['source_text']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='color:{colors['text_tertiary']};font-size:{typography['font_size_sm']};'>*注：本次回答未检索匹配到任何符合距离阈值的知识库内容，完全依靠系统兜底或大模型闲聊输出。*</div>", unsafe_allow_html=True)
