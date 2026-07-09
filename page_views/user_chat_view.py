# -*- coding: utf-8 -*-
"""
AIZS 用户咨询端 - 智能咨询视图
"""
import os
import streamlit as st
import time
from config import settings
from repositories import sqlite_repository
from services.chat_service import ChatService
from utils.logger import logger
from utils.display_utils import format_confidence
from utils.ui_utils import render_page_header, render_empty_state

# 实例化对话服务
@st.cache_resource
def get_chat_service():
    return ChatService()

def render():
    chat_service = get_chat_service()

    # 确保会话状态初始化
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None

    # --- 侧边栏：历史会话管理 (这会追加入主菜单下方) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏳ 会话管理")

    # 新建会话按钮
    if st.sidebar.button("➕ 新建咨询会话", use_container_width=True, type="primary"):
        try:
            new_id = chat_service.start_new_session()
            st.session_state.current_session_id = new_id
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"创建会话失败: {e}")

    # 获取历史会话列表
    sessions = sqlite_repository.list_chat_sessions()

    if not sessions:
        st.sidebar.info("暂无历史会话记录")
    else:
        st.sidebar.markdown("#### 💬 历史会话列表")
        for sess in sessions:
            col1, col2 = st.sidebar.columns([5, 1])
            is_active = (sess["session_id"] == st.session_state.current_session_id)
            btn_label = f"💬 {sess['title']}"

            with col1:
                if st.button(
                    btn_label,
                    key=f"active_{sess['session_id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.current_session_id = sess["session_id"]
                    st.rerun()

            with col2:
                if st.button("🗑️", key=f"del_{sess['session_id']}", help="删除此会话"):
                    sqlite_repository.delete_chat_session(sess["session_id"])
                    if st.session_state.current_session_id == sess["session_id"]:
                        st.session_state.current_session_id = None
                    st.rerun()

    # --- 主界面 ---
    render_page_header(
        "💬 AIZS 智能咨询",
        "基于知识库来源引用的校园问答助手。"
    )

    # 快速检查 API 状态
    if not settings.DASHSCOPE_API_KEY:
        st.warning("⚠️ **温馨提示：** 未配置大模型 API 密钥（DASHSCOPE_API_KEY 为空），系统目前仅能读取已存的历史会话。若要进行智能问答或导入文档，请在根目录配置 `.env` 文件。")

    # 注入来源样式
    st.markdown("""
    <style>
        .source-box {
            background-color: #f8faff;
            border-left: 4px solid #2a5298;
            padding: 12px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .source-box strong {
            color: #1e3c72;
        }
        .source-box .source-text {
            color: #5a6e85;
            font-size: 0.83rem;
            margin-top: 4px;
        }
    </style>
    """, unsafe_allow_html=True)

    # 加载展示当前会话的历史消息
    if st.session_state.current_session_id:
        current_sess_detail = next((s for s in sessions if s["session_id"] == st.session_state.current_session_id), None)
        if current_sess_detail:
            st.caption(f"当前会话：**{current_sess_detail['title']}** (创建时间：{current_sess_detail['created_at']})")

        messages = sqlite_repository.get_chat_messages(st.session_state.current_session_id)

        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    if msg.get("intent_name"):
                        conf_text = format_confidence(msg.get("intent_confidence"))
                        st.markdown(f'<p style="color: #4f5f6f; font-size: 0.85rem; margin-top: -10px; margin-bottom: 8px;">🎯 当前识别意图：<b>{msg["intent_name"]}咨询</b> (置信度: {conf_text})</p>', unsafe_allow_html=True)

                    sources = sqlite_repository.get_message_sources(msg["message_id"])
                    if sources:
                        with st.expander("🔍 信息来源"):
                            for idx, src in enumerate(sources):
                                page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong>
                                    <div class="source-text">{src['source_text']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("📭 当前知识库未检索到足够相关依据，请以学校官方通知为准。")

                    # 满意度反馈
                    feedback = sqlite_repository.get_feedback_by_message_id(msg["message_id"])
                    col_fb1, col_fb2, _ = st.columns([1.8, 1.8, 6.4])
                    like_active = feedback and feedback["rating"] == "like"
                    dislike_active = feedback and feedback["rating"] == "dislike"

                    with col_fb1:
                        if st.button("👍 有帮助" + (" (已选)" if like_active else ""), key=f"like_{msg['message_id']}", use_container_width=True):
                            sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.current_session_id, "like")
                            st.toast("感谢您的反馈！")
                            time.sleep(0.4)
                            st.rerun()
                    with col_fb2:
                        if st.button("👎 不准确" + (" (已选)" if dislike_active else ""), key=f"dislike_{msg['message_id']}", use_container_width=True):
                            sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.current_session_id, "dislike", "用户反馈回答不准确")
                            st.toast("已记录反馈，我们将持续改进！")
                            time.sleep(0.4)
                            st.rerun()
    else:
        render_empty_state(
            title="暂无活动会话",
            description='请在左侧栏选择一个历史会话，或点击“新建咨询会话”开始聊天。',
            icon="💬"
        )

    # 对话输入框
    user_input = st.chat_input("请输入您想咨询的校园问题...")

    if user_input:
        if not st.session_state.current_session_id:
            try:
                new_id = chat_service.start_new_session()
                st.session_state.current_session_id = new_id
            except Exception as e:
                st.error(f"初始化会话失败: {e}")
                st.stop()

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            retrieved_sources = []

            message_placeholder.markdown("*正在检索知识库并思考中...*")

            try:
                chat_stream = chat_service.handle_chat_flow(st.session_state.current_session_id, user_input)
                intent_placeholder = st.empty()

                for chunk in chat_stream:
                    if chunk["type"] == "intent":
                        intent_data = chunk["data"]
                        conf_text = format_confidence(intent_data.get("confidence"))
                        intent_placeholder.markdown(f'<p style="color: #4f5f6f; font-size: 0.85rem; margin-bottom: 5px;">🎯 识别到意图：<b>{intent_data["intent_name"]}咨询</b> (置信度: {conf_text})</p>', unsafe_allow_html=True)
                    elif chunk["type"] == "sources":
                        retrieved_sources = chunk["data"]
                    elif chunk["type"] == "text":
                        full_response += chunk["data"]
                        message_placeholder.markdown(full_response + "▌")
                    elif chunk["type"] == "error":
                        st.error(chunk["data"])
                        st.stop()

                message_placeholder.markdown(full_response)

                if retrieved_sources:
                    with st.expander("🔍 信息来源", expanded=True):
                        for idx, src in enumerate(retrieved_sources):
                            page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                            st.markdown(f"""
                            <div class="source-box">
                                <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong>
                                <div class="source-text">{src['source_text']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("📭 当前知识库未检索到足够相关依据，请以学校官方通知为准。")

                st.rerun()
            except Exception as e:
                st.error(f"处理咨询失败: {e}")
                logger.error(f"处理咨询异常: {e}")
