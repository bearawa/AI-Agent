import streamlit as st
import datetime
from services.analytics_service import AnalyticsService
from repositories import sqlite_repository
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav
from utils.display_utils import format_confidence, format_ms

# 初始化数据统计服务
@st.cache_resource
def get_analytics_service():
    return AnalyticsService()

analytics_service = get_analytics_service()

# 页面基本配置
st.set_page_config(
    page_title="会话日志 - AIZS 管理后台",
    page_icon="📜",
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
        background: linear-gradient(135deg, #1f4068 0%, #162447 100%);
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
    .log-box {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #eef2f3;
    }
    .meta-tag {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-right: 5px;
    }
    .tag-intent { background-color: #e3f2fd; color: #0d47a1; }
    .tag-source { background-color: #e8f5e9; color: #1b5e20; }
    .tag-nosource { background-color: #ffebee; color: #c62828; }
    .tag-time { background-color: #eceff1; color: #37474f; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📜 会话审计日志</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">系统管理员可在此页面检索、审计全部历史咨询对话，深入还原每次问答的匹配耗时、改写细节及知识库切片引用证据。</p>', unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：会话日志")
render_logout_button()

# --- 筛选控制面板 ---
st.markdown("### 🔍 筛选条件")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    
    # 1. 日期范围筛选
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

    # 2. 意图分类筛选
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

    # 3. 来源筛选
    with c3:
        source_options = {
            "全部": None,
            "有参考来源": 1,
            "无参考来源": 0
        }
        selected_source_cn = st.selectbox("包含参考来源：", list(source_options.keys()))
        selected_source_val = source_options[selected_source_cn]

    # 4. 反馈与关键词
    with c4:
        is_disliked = st.checkbox("🔍 只看点踩(dislike)反馈")
        search_keyword = st.text_input("关键字检索(提问/回答)：", placeholder="请输入搜索词...")

# 2. 执行数据检索
logs = analytics_service.get_session_logs(
    start_date=start_date,
    end_date=end_date,
    intent=selected_intent_en,
    has_source=selected_source_val,
    is_disliked=is_disliked,
    search_keyword=search_keyword
)

st.markdown("---")
st.markdown(f"### 📋 查询结果 (共 {len(logs)} 条记录)")

if not logs:
    st.info("💡 暂无符合筛选条件的会话日志。")
else:
    # 循环遍历会话日志并渲染
    for idx, log in enumerate(logs):
        msg_id = log["message_id"]
        session_id = log["session_id"]
        time_str = log["time"]
        user_question = log["user_question"] if log["user_question"] else "（未知提问）"
        assistant_answer = log["assistant_answer"] if log["assistant_answer"] else "（无回答内容）"
        intent_name = log.get("intent_name", "其他")
        confidence = log.get("intent_confidence")
        rewritten = log.get("rewritten_query")
        has_src = log.get("has_source")
        time_ms = log.get("response_time_ms")
        rating = log.get("feedback_rating")
        comment = log.get("feedback_comment")

        # 1. 意图分类名称空值兼容处理
        if not intent_name or not str(intent_name).strip():
            intent_name_text = "未识别"
        else:
            intent_name_text = str(intent_name)

        # 2. 置信度空值兼容处理
        confidence_text = format_confidence(confidence)

        # 3. 来源状态及标签兼容处理
        if has_src == 1:
            source_text = "有来源"
            source_tag = "tag-source"
        else:
            source_text = "无来源"
            source_tag = "tag-nosource"

        # 4. 响应耗时空值兼容处理
        time_ms_text = format_ms(time_ms)

        # 5. 用户反馈状态兼容处理
        rating_str = "无反馈"
        if rating == "like":
            rating_str = "👍 赞"
        elif rating == "dislike":
            rating_str = f"👎 踩 ({comment if comment else '未填意见'})"

        # 展示在一行卡片 header 中
        summary_title = f"⏱️ {time_str} | 问：{user_question[:25]}..."
        if len(user_question) > 25:
            summary_title += "..."

        with st.expander(summary_title):
            # 顶部标签排版
            st.markdown(f"""
            <span class="meta-tag tag-intent">🎯 意图：{intent_name_text} ({confidence_text} 置信度)</span>
            <span class="meta-tag {source_tag}">📁 匹配引用：{source_text}</span>
            <span class="meta-tag tag-time">⚡ 耗时：{time_ms_text}</span>
            <span class="meta-tag tag-time">💬 反馈：{rating_str}</span>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**会话 ID:** `{session_id}`")
            st.markdown("---")
            
            # 对话明细展现
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
            
            # 信息来源拉取展示
            if has_src:
                st.markdown("**📖 引用的知识库来源切片明细：**")
                sources = sqlite_repository.get_message_sources(msg_id)
                if not sources:
                    st.caption("数据库中暂无该消息的来源切片索引记录。")
                else:
                    for src_idx, src in enumerate(sources, 1):
                        page_str = f"第 {src['page_number']} 页" if src['page_number'] is not None else f"片段 {src['chunk_index']}"
                        st.markdown(f"""
                        <div style="background-color: #f0f4f8; padding: 10px; border-radius: 4px; border-left: 4px solid #1f4068; margin-bottom: 6px;">
                            <strong>[{src_idx}] {src['file_name']} ({page_str}) | 相似度匹配值：{(1-src['similarity_distance'])*100:.1f}%</strong><br/>
                            <p style="font-size: 0.85rem; color: #34495e; margin: 5px 0 0 0;">{src['source_text']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("*注：本次回答未检索匹配到任何符合距离阈值的知识库内容，完全依靠系统兜底或大模型闲聊输出。*")
