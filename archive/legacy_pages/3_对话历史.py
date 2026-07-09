import streamlit as st
from repositories import sqlite_repository
from utils.logger import logger
from utils.auth_utils import render_sidebar_nav

# 页面配置
st.set_page_config(
    page_title="对话历史 - AIZS",
    page_icon="⏳",
    layout="wide"
)

# 渲染统一侧边栏导航
render_sidebar_nav()


# 自定义 premium 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%);
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
    .meta-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 20px;
        border-top: 4px solid #FF4B2B;
    }
    .source-box {
        background-color: #f0f4f8;
        border-left: 4px solid #FF4B2B;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">⏳ 对话历史档案库</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">在这里查阅历史咨询会话的完整对话轨迹、消息数量、时间印记及底层的知识检索来源出处。</p>', unsafe_allow_html=True)

# 1. 查询所有历史会话
sessions = sqlite_repository.list_chat_sessions()

if not sessions:
    st.info("💡 暂无历史对话档案。")
else:
    # 2. 构造会话选择列表选项
    session_options = []
    session_id_map = {}
    
    for sess in sessions:
        # 格式：[更新日期] 会话标题 (共 X 条消息)
        date_part = sess["updated_at"][:10]
        label = f"[{date_part}] {sess['title']} (共 {sess['message_count']} 条消息)"
        session_options.append(label)
        session_id_map[label] = sess["session_id"]

    # 分栏布局：左侧会话选择及基础指标，右侧聊天流水重播
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### 📁 选择归档会话")
        selected_label = st.selectbox(
            "选择要浏览的咨询历史记录：",
            options=session_options,
            index=0
        )
        
        # 获取选中的会话 ID
        selected_session_id = session_id_map[selected_label]
        
        # 获取该会话的详细指标
        selected_sess_detail = next(s for s in sessions if s["session_id"] == selected_session_id)
        
        # 渲染元数据卡片
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
        
        # 提供在历史页面删除该会话的快捷入口
        if st.button("🗑️ 删除本条会话记录", type="secondary", use_container_width=True):
            sqlite_repository.delete_chat_session(selected_session_id)
            st.success("成功删除会话！")
            st.rerun()

    with col_right:
        st.markdown("### 💬 历史对话轨迹重现")
        
        # 实时从 SQLite 查询该会话的历史消息列表
        messages = sqlite_repository.get_chat_messages(selected_session_id)
        
        if not messages:
            st.warning("该会话没有包含任何消息记录")
        else:
            # 渲染消息流水气泡
            for msg in messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    # 如果是助手，提取并渲染来源
                    if msg["role"] == "assistant":
                        sources = sqlite_repository.get_message_sources(msg["message_id"])
                        if sources:
                            with st.expander("🔍 本次回答的信息来源"):
                                for idx, src in enumerate(sources):
                                    page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                                    st.markdown(f"""
                                    <div class="source-box">
                                        <strong>[{idx+1}] 出处：{src['file_name']} ({page_str}) | 相似度匹配值：{(1 - src['similarity_distance'])*100:.1f}%</strong><br/>
                                        <small style="color: #4a5e6d;">{src['source_text']}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
