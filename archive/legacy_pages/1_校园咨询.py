import streamlit as st
from config import settings
from repositories import sqlite_repository
from services.chat_service import ChatService
from utils.logger import logger
from utils.display_utils import format_confidence
from utils.auth_utils import render_sidebar_nav

# 初始化对话服务
@st.cache_resource
def get_chat_service():
    return ChatService()

chat_service = get_chat_service()

# 页面基本设置
st.set_page_config(
    page_title="校园咨询 - AIZS",
    page_icon="🏫",
    layout="wide"
)

# 渲染统一侧边栏导航
render_sidebar_nav()


# 注入自定义 Premium 样式
st.markdown("""
<style>
    /* 全局背景和卡片玻璃质感 */
    .stApp {
        background-color: #f7f9fc;
    }
    .css-1y4q58y {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 20px;
    }
    /* 标题质感 */
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #5a6e85;
        margin-bottom: 25px;
    }
    /* 会话栏按钮 */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    /* 聊天来源排版 */
    .source-box {
        background-color: #f0f4f8;
        border-left: 4px solid #2a5298;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 确保会话状态初始化
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# --- 侧边栏：历史会话管理 ---
st.sidebar.markdown("### 🏫 导航与会话")

# 新建会话按钮
if st.sidebar.button("➕ 新建咨询会话", use_container_width=True, type="primary"):
    # 在服务中新建一个会话并设为当前会话
    try:
        new_id = chat_service.start_new_session()
        st.session_state.current_session_id = new_id
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"创建会话失败: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⏳ 历史会话")

# 获取历史会话列表
sessions = sqlite_repository.list_chat_sessions()

if not sessions:
    st.sidebar.info("暂无历史会话记录")
else:
    for sess in sessions:
        # 为每个会话创建两列，一列显示标题，一列放置删除按钮
        col1, col2 = st.sidebar.columns([5, 1])
        
        # 判断当前循环的会话是否是被选中的那个，选中则高亮（使用 st.button 的样式区分）
        is_active = (sess["session_id"] == st.session_state.current_session_id)
        btn_label = f"💬 {sess['title']}"
        
        with col1:
            if st.button(
                btn_label, 
                key=f"active_{sess['session_id']}", 
                use_container_width=True,
                type="secondary" if not is_active else "primary"
            ):
                st.session_state.current_session_id = sess["session_id"]
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"del_{sess['session_id']}", help="删除此会话"):
                sqlite_repository.delete_chat_session(sess["session_id"])
                # 如果删除的是当前处于活动状态的会话，重置活动会话ID为 None
                if st.session_state.current_session_id == sess["session_id"]:
                    st.session_state.current_session_id = None
                st.rerun()

# --- 主界面 ---
st.markdown('<h1 class="main-title">AIZS｜校园智能咨询平台</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">欢迎使用 AIZS 校园智能咨询平台，您可以咨询有关奖学金、招生政策、校纪校规等各类问题。</p>', unsafe_allow_html=True)

# 快速检查 API 状态
if not settings.DASHSCOPE_API_KEY:
    st.warning("⚠️ **温馨提示：** 未配置大模型 API 密钥（DASHSCOPE_API_KEY 为空），系统目前仅能读取已存的历史会话。若要进行智能问答或导入文档，请在根目录创建并配置 `.env` 文件。")

# 加载展示当前会话的历史消息
if st.session_state.current_session_id:
    # 查找会话详情
    current_sess_detail = next((s for s in sessions if s["session_id"] == st.session_state.current_session_id), None)
    if current_sess_detail:
        st.caption(f"当前会话：**{current_sess_detail['title']}** (创建时间：{current_sess_detail['created_at']})")
    
    messages = sqlite_repository.get_chat_messages(st.session_state.current_session_id)
    
    # 循环展示历史消息
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # 如果是助手的回答，去 SQLite 查询对应的相关原文来源
            if msg["role"] == "assistant":
                # 轻量展示识别到的意图
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
                                <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong><br/>
                                <small style="color: #4a5e6d;">{src['source_text']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                # 满意度反馈组件
                feedback = sqlite_repository.get_feedback_by_message_id(msg["message_id"])
                col_fb1, col_fb2, _ = st.columns([1.8, 1.8, 6.4])
                like_active = feedback and feedback["rating"] == "like"
                dislike_active = feedback and feedback["rating"] == "dislike"
                
                with col_fb1:
                    if st.button("👍 有帮助" + (" (已选)" if like_active else ""), key=f"like_{msg['message_id']}", use_container_width=True):
                        sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.current_session_id, "like")
                        st.toast("感谢您的反馈！")
                        import time
                        time.sleep(0.4)
                        st.rerun()
                with col_fb2:
                    if st.button("👎 不准确" + (" (已选)" if dislike_active else ""), key=f"dislike_{msg['message_id']}", use_container_width=True):
                        sqlite_repository.save_or_update_feedback(msg["message_id"], st.session_state.current_session_id, "dislike", "用户反馈回答不准确")
                        st.toast("已记录反馈，我们将持续改进！")
                        import time
                        time.sleep(0.4)
                        st.rerun()
else:
    # 没有选中会话时的欢迎语
    st.info("💡 请在左侧栏选择一个历史会话，或点击“新建咨询会话”开始聊天。")

# --- 对话输入框 ---
user_input = st.chat_input("请输入您想咨询的校园问题...")

if user_input:
    # 如果还没有选择任何会话，则自动创建一个新会话
    if not st.session_state.current_session_id:
        try:
            new_id = chat_service.start_new_session()
            st.session_state.current_session_id = new_id
        except Exception as e:
            st.error(f"初始化会话失败: {e}")
            st.stop()

    # 1. 立即显示用户的问题
    # 渲染历史（在 rerun 后会重绘，这里先画用户的问题增强响应体验）
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. 渲染助手的流式回答框
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        retrieved_sources = []
        
        # 加载中状态
        message_placeholder.markdown("*正在检索知识库并思考中...*")

        try:
            # 开启聊天流
            chat_stream = chat_service.handle_chat_flow(st.session_state.current_session_id, user_input)
            
            intent_placeholder = st.empty()
            
            for chunk in chat_stream:
                if chunk["type"] == "intent":
                    # 提取识别意图
                    intent_data = chunk["data"]
                    conf_text = format_confidence(intent_data.get("confidence"))
                    intent_placeholder.markdown(f'<p style="color: #4f5f6f; font-size: 0.85rem; margin-bottom: 5px;">🎯 识别到意图：<b>{intent_data["intent_name"]}咨询</b> (置信度: {conf_text})</p>', unsafe_allow_html=True)
                elif chunk["type"] == "sources":
                    # 抓取向量库检索到的原文片段
                    retrieved_sources = chunk["data"]
                elif chunk["type"] == "text":
                    full_response += chunk["data"]
                    # 流式渲染当前打字内容加上闪烁光标
                    message_placeholder.markdown(full_response + "▌")
                elif chunk["type"] == "error":
                    st.error(chunk["data"])
                    st.stop()
            
            # 流式结束，移除光标
            message_placeholder.markdown(full_response)
            
            # 若有检索来源，在当前回答下方直接画出折叠框
            if retrieved_sources:
                with st.expander("🔍 信息来源", expanded=True):
                    for idx, src in enumerate(retrieved_sources):
                        page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                        st.markdown(f"""
                        <div class="source-box">
                            <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong><br/>
                            <small style="color: #4a5e6d;">{src['source_text']}</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # 3. 对话结束后进行重新加载，刷新会话标题及聊天面板
            st.rerun()

        except Exception as e:
            st.error(f"❌ 对话时发生异常: {str(e)}")
            logger.error(f"页面对话流执行失败: {e}")
