# -*- coding: utf-8 -*-
"""
AIZS 用户咨询端 - 对话历史视图
"""
import streamlit as st
import os
from repositories import sqlite_repository
from utils.ui_utils import render_page_header, render_empty_state

def render():
    # 自定义样式
    st.markdown("""
    <style>
        .meta-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-bottom: 20px;
            border-top: 4px solid #1e3c72;
        }
        .meta-card h4 {
            margin: 0 0 10px 0;
            color: #1e3c72;
        }
        .meta-card p {
            margin: 4px 0;
            font-size: 0.9rem;
            color: #4a5568;
        }
        .source-box {
            background-color: #f8faff;
            border-left: 4px solid #1e3c72;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    render_page_header(
        "⏳ 对话历史档案库",
        "在这里查阅历史咨询会话的完整对话轨迹、消息数量、时间印记及底层的知识检索来源出处。"
    )

    # 1. 查询所有历史会话
    sessions = sqlite_repository.list_chat_sessions()

    if not sessions:
        render_empty_state(
            title="暂无历史对话档案",
            description="请先在智能咨询页面进行对话，对话记录将自动保存在这里。",
            icon="⏳"
        )
    else:
        # 2. 构造会话选择列表选项
        session_options = []
        session_id_map = {}

        for sess in sessions:
            date_part = sess["updated_at"][:10]
            label = f"[{date_part}] {sess['title']} (共 {sess['message_count']} 条消息)"
            session_options.append(label)
            session_id_map[label] = sess["session_id"]

        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.markdown("### 📁 选择归档会话")
            selected_label = st.selectbox(
                "选择要浏览的咨询历史记录：",
                options=session_options,
                index=0
            )

            selected_session_id = session_id_map[selected_label]
            selected_sess_detail = next(s for s in sessions if s["session_id"] == selected_session_id)

            st.markdown(f"""
            <div class="meta-card">
                <h4>📊 会话基本指标</h4>
                <p>🔑 <strong>会话标识：</strong><code style='font-size:0.8rem;'>{selected_session_id}</code></p>
                <p>📝 <strong>当前标题：</strong> {selected_sess_detail['title']}</p>
                <p>📅 <strong>创建时间：</strong> {selected_sess_detail['created_at']}</p>
                <p>🔄 <strong>最后更新：</strong> {selected_sess_detail['updated_at']}</p>
                <p>💬 <strong>消息总量：</strong> {selected_sess_detail['message_count']} 条消息</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🗑️ 删除本条会话记录", type="secondary", use_container_width=True):
                sqlite_repository.delete_chat_session(selected_session_id)
                st.success("成功删除会话！")
                st.rerun()

        with col_right:
            st.markdown("### 💬 历史对话轨迹重现")
            messages = sqlite_repository.get_chat_messages(selected_session_id)

            if not messages:
                render_empty_state(
                    title="该会话暂无消息记录",
                    description="此会话没有保存任何对话内容。",
                    icon="💬"
                )
            else:
                for msg in messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        if msg["role"] == "assistant":
                            sources = sqlite_repository.get_message_sources(msg["message_id"])
                            if sources:
                                with st.expander("🔍 本次回答的信息来源"):
                                    for idx, src in enumerate(sources):
                                        page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                                        st.markdown(f"""
                                        <div class="source-box">
                                            <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong><br/>
                                            <small style="color: #5a6e85;">{src['source_text']}</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.info("📭 本次回答未检索到知识库来源。")
