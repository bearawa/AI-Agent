# -*- coding: utf-8 -*-
"""
AIZS 用户咨询端 - Agent 智能演示视图
"""
import streamlit as st
import time
import json
from config import settings
from repositories import sqlite_repository
from services.agent_service import AgentService
from utils.logger import logger
from utils.display_utils import format_confidence
from utils.ui_utils import render_page_header, render_empty_state

# 初始化 Agent 服务
@st.cache_resource
def get_agent_service():
    return AgentService()

def render():
    agent_service = get_agent_service()

    # 确保会话状态初始化
    if "agent_session_id" not in st.session_state:
        st.session_state.agent_session_id = None

    # 自定义样式
    st.markdown("""
    <style>
        .trace-container {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 16px;
            border-left: 5px solid #1e3c72;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 15px;
        }
        .trace-step {
            font-family: 'Consolas', monospace;
            font-size: 0.85rem;
            margin-bottom: 8px;
            color: #2c3e50;
            padding: 6px 0;
            border-bottom: 1px solid #f0f2f6;
        }
        .trace-step:last-child {
            border-bottom: none;
        }
        .quality-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
            color: white;
            margin-right: 5px;
        }
        .badge-high { background-color: #2ecc71; }
        .badge-low { background-color: #e74c3c; }

        .source-box {
            background-color: #f8faff;
            border-left: 4px solid #1e3c72;
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }
        .scenarios-box {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 14px;
            border: 1px solid #e1e4e8;
            margin-bottom: 15px;
        }
        .tool-result-card {
            background: #f0f8ff;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #d0e0f0;
            margin: 8px 0;
        }
        .tool-error-card {
            background: #fff5f5;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #ffd0d0;
            margin: 8px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    render_page_header(
        "🤖 AIZS Agent 智能演示",
        "本页面为演示页，展示 Agent 的多步任务拆分与执行、多工具协同、主动澄清追问、Agent 执行轨迹展示及回答质量评估功能。"
    )

    if not settings.DASHSCOPE_API_KEY:
        st.warning("⚠️ **温馨提示：** 未配置大模型 API 密钥（DASHSCOPE_API_KEY 为空），系统目前仅能读取已存的历史会话。若要进行智能问答，请在根目录配置 `.env` 文件。")

    # 获取历史会话列表
    sessions = sqlite_repository.list_chat_sessions()
    agent_sessions = [s for s in sessions if "Agent" in s["title"] or s["title"] == "新建会话"]

    # --- 侧边栏：历史 Agent 会话管理 (追加入主菜单下方) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 Agent 会话")

    # 新建会话按钮
    if st.sidebar.button("➕ 新建 Agent 会话", use_container_width=True, type="primary"):
        try:
            new_id = sqlite_repository.create_chat_session("Agent 演示会话")
            st.session_state.agent_session_id = new_id
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"创建会话失败: {e}")

    if not agent_sessions:
        st.sidebar.info("暂无历史 Agent 会话记录，请点击上方按钮新建")
    else:
        st.sidebar.markdown("#### ⏳ 历史 Agent 会话")
        for sess in agent_sessions:
            col1, col2 = st.sidebar.columns([5, 1])
            is_active = (sess["session_id"] == st.session_state.agent_session_id)
            with col1:
                if st.button(
                    f"💬 {sess['title'][:12]}...",
                    key=f"agent_sess_{sess['session_id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.agent_session_id = sess["session_id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_agent_sess_{sess['session_id']}", help="删除此会话"):
                    sqlite_repository.delete_chat_session(sess["session_id"])
                    if st.session_state.agent_session_id == sess["session_id"]:
                        st.session_state.agent_session_id = None
                    st.rerun()

    # 顶部场景测试区
    st.markdown("### 💡 快捷场景测试（免手动输入）")
    with st.container():
        st.markdown('<div class="scenarios-box">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        preset_query = None

        with c1:
            if st.button("复合问题测试 ➔\n\n新生报到要准备什么？明天天气怎么样？", use_container_width=True, help="同时触发 RAG 检索报到材料和调用天气工具"):
                preset_query = "新生报到要准备什么？明天天气怎么样？"
        with c2:
            if st.button("主动澄清测试 ➔\n\n什么时候报名？", use_container_width=True, help="测试在没有明确上下文时触发澄清追问"):
                preset_query = "什么时候报名？"
        with c3:
            if st.button("常规检索测试 ➔\n\n图书馆几点关门？", use_container_width=True, help="测试普通 RAG 或是校园状态查询"):
                preset_query = "图书馆几点关门？"

        st.markdown("<p style='font-size:0.8rem;color:#7f8c8d;margin-top:5px;'>*提示：点击快捷按钮将自动建立或在此会话下发送指定提问。*</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 确保有活动会话
    if not st.session_state.agent_session_id:
        if agent_sessions:
            st.session_state.agent_session_id = agent_sessions[0]["session_id"]
        else:
            try:
                st.session_state.agent_session_id = sqlite_repository.create_chat_session("Agent 演示会话")
            except Exception as e:
                st.error(f"初始化 Agent 演示会话失败: {e}")
                st.stop()

    # 加载并渲染当前会话的历史消息
    if st.session_state.agent_session_id:
        messages = sqlite_repository.get_chat_messages(st.session_state.agent_session_id)

        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                if msg["role"] == "assistant":
                    if msg.get("intent_name"):
                        conf_text = format_confidence(msg.get("intent_confidence"))
                        st.markdown(f'<p style="color: #555; font-size: 0.8rem; margin-top:-10px;">🎯 识别意图：<b>{msg["intent_name"]}咨询</b> (置信度: {conf_text})</p>', unsafe_allow_html=True)

                    traces = sqlite_repository.get_agent_traces(st.session_state.agent_session_id, msg["message_id"])
                    if traces:
                        with st.expander("🛤️ Agent 执行轨迹与调用详情", expanded=False):
                            st.markdown('<div class="trace-container">', unsafe_allow_html=True)
                            for t in traces:
                                icon = "⚙️"
                                if t["step_type"] in ["tool_call", "tool_result"]:
                                    icon = "🛠️"
                                elif t["step_type"] == "clarify":
                                    icon = "❓"
                                elif t["step_type"] == "generate":
                                    icon = "✍️"

                                st.markdown(f"""
                                <div class="trace-step">
                                    <strong>{icon} 步骤 {t['step_index']}: {t['step_title']}</strong><br/>
                                    <span style="color: #666; font-size: 0.8rem;">{t['step_detail']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    sources = sqlite_repository.get_message_sources(msg["message_id"])
                    if sources:
                        with st.expander("📖 知识库引用来源 (RAG Source)", expanded=False):
                            for src_idx, src in enumerate(sources, 1):
                                page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                                st.markdown(f"""
                                <div class="source-box">
                                    <strong>[{src_idx}] {src['file_name']} ({page_str}) | 余弦距离：{src['similarity_distance']:.4f}</strong><br/>
                                    <span style="color:#555;">{src['source_text']}</span>
                                </div>
                                """, unsafe_allow_html=True)

                    # 质量评估详情
                    with sqlite_repository.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM quality_evaluations WHERE message_id = ?", (msg["message_id"],))
                        eval_row = cursor.fetchone()

                    if eval_row:
                        eval_dict = dict(eval_row)
                        score = eval_dict["score"]
                        is_low = eval_dict["is_low_quality"]
                        issues_list = []
                        try:
                            issues_list = json.loads(eval_dict["issues"])
                        except:
                            pass
                        suggestion = eval_dict["suggestion"]

                        with st.expander("⭐ 回答质量评估结果", expanded=False):
                            c_score, c_info = st.columns([1, 4])
                            with c_score:
                                st.metric("质量评估分", f"{score} / 5")
                            with c_info:
                                badge_class = "badge-low" if is_low == 1 else "badge-high"
                                badge_text = "⚠️ 低质量回答" if is_low == 1 else "✅ 高质量回答"
                                st.markdown(f'<span class="quality-badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
                                if issues_list:
                                    with st.expander("🔍 识别问题与改进建议"):
                                        st.markdown(f"**识别问题:** {', '.join(issues_list)}")
                                        st.markdown(f"**改进建议:** {suggestion}")
                                else:
                                    st.markdown(f"**改进建议:** {suggestion}")
                                st.caption(f"评估器类型: {eval_dict['evaluator']} | 时间: {eval_dict['created_at']}")

                    # 反馈组件
                    feedback = sqlite_repository.get_feedback_by_message_id(msg["message_id"])
                    col_fb1, col_fb2, _ = st.columns([1.5, 1.5, 7.0])
                    like_active = feedback and feedback["rating"] == "like"
                    dislike_active = feedback and feedback["rating"] == "dislike"

                    with col_fb1:
                        if st.button("👍 有帮助" + (" (已选)" if like_active else ""), key=f"like_{msg['message_id']}", use_container_width=True):
                            sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.agent_session_id, "like")
                            st.toast("感谢您的反馈！已重新计算质量分。")
                            time.sleep(0.4)
                            st.rerun()
                    with col_fb2:
                        if st.button("👎 不准确" + (" (已选)" if dislike_active else ""), key=f"dislike_{msg['message_id']}", use_container_width=True):
                            sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.agent_session_id, "dislike", "用户反馈回答不准确")
                            st.toast("反馈已记录，并且评估机制已被触发，该回答已被标记为低质量！")
                            time.sleep(0.4)
                            st.rerun()

    # 接受输入
    user_query = st.chat_input("请输入校园问题或点击上方的快捷测试场景...")
    if preset_query:
        user_query = preset_query

    if user_query:
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            trace_placeholder = st.expander("🛤️ Agent 实时执行状态与轨迹", expanded=True)
            trace_list = []

            def render_traces():
                with trace_placeholder:
                    for t in trace_list:
                        icon = "🛠️" if "工具" in t["step_title"] or "调用" in t["step_title"] else "⚙️"
                        if "澄清" in t["step_title"]:
                            icon = "❓"
                        st.markdown(f"**{icon} 步骤 {t['step_index']}: {t['step_title']}** - *{t['step_detail']}*")

            text_placeholder = st.empty()
            text_placeholder.markdown("*Agent 正在深入推理中，请稍候...*")
            sources_placeholder = st.empty()
            quality_placeholder = st.empty()
            full_text = ""

            try:
                # 获取 Agent 对话流
                agent_service = get_agent_service()
                agent_flow = agent_service.handle_agent_chat_flow(st.session_state.agent_session_id, user_query)

                for chunk in agent_flow:
                    if chunk["type"] == "intent":
                        pass
                    elif chunk["type"] == "trace":
                        trace_list.append(chunk["data"])
                        render_traces()
                    elif chunk["type"] == "sources":
                        srcs = chunk["data"]
                        if srcs:
                            with sources_placeholder.expander("📖 实时匹配引用来源 (RAG Source)", expanded=False):
                                for idx, s in enumerate(srcs, 1):
                                    page_str = f"第 {s['page_number']} 页" if s['page_number'] is not None else "无页码"
                                    page_info = s.get('page_info') or page_str
                                    st.markdown(f"""
                                    <div class="source-box">
                                        <strong>[{idx}] {s['file_name']} ({page_info})</strong><br/>
                                        <span>{s['source_text']}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                    elif chunk["type"] == "text":
                        full_text += chunk["data"]
                        text_placeholder.markdown(full_text + "▌")
                    elif chunk["type"] == "quality":
                        q = chunk["data"]
                        with quality_placeholder.expander("⭐ 回答质量评估结果", expanded=True):
                            c_sc, c_if = st.columns([1, 4])
                            with c_sc:
                                st.metric("质量评估分", f"{q['score']} / 5")
                            with c_if:
                                badge_style = "badge-low" if q["is_low_quality"] else "badge-high"
                                badge_lbl = "⚠️ 低质量回答" if q["is_low_quality"] else "✅ 高质量回答"
                                st.markdown(f'<span class="quality-badge {badge_style}">{badge_lbl}</span>', unsafe_allow_html=True)
                                if q["issues"]:
                                    with st.expander("🔍 检测问题与改进建议"):
                                        st.markdown(f"**检测问题:** {', '.join(q['issues'])}")
                                        st.markdown(f"**改进建议:** {q['suggestion']}")
                                else:
                                    st.markdown(f"**改进建议:** {q['suggestion']}")
                    elif chunk["type"] == "error":
                        st.error(f"❌ 处理出错: {chunk['data']}")

                text_placeholder.markdown(full_text)
                st.toast("问答处理完毕！已完成执行轨迹、工具调用日志、回答质量评估数据的写入。")
                time.sleep(1.2)
                st.rerun()

            except Exception as flow_err:
                logger.error(f"演示流式发生未捕获异常: {flow_err}")
                st.error(f"❌ 处理提问时失败: {flow_err}")
