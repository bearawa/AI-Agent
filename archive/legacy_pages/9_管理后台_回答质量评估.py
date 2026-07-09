import streamlit as st
import json
from repositories import sqlite_repository
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav

# 页面配置
st.set_page_config(
    page_title="回答质量评估 - AIZS 管理后台",
    page_icon="⭐",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# Premium 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #7f8c8d;
        margin-bottom: 25px;
    }
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

st.markdown('<h1 class="main-title">⭐ 回答质量审计与优化</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">系统管理员可在此页面集中审计客服系统的每一次回答质量，查看评分、分析低质量问答的缺陷（无来源风险、调用失败、点踩等），并提取优化建议。</p>', unsafe_allow_html=True)

# 侧边栏
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：回答质量评估")
render_logout_button()

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

# 执行查询
evals = sqlite_repository.list_quality_evaluations(
    limit=limit_val,
    is_low_quality=is_low_quality_val,
    min_score=min_s,
    max_score=max_s
)

st.markdown("---")
st.markdown(f"### 📋 质量分析列表 (共 {len(evals)} 条记录)")

if not evals:
    st.info("💡 没有找到符合当前过滤条件的质量评估记录。")
else:
    for idx, ev in enumerate(evals):
        eval_id = ev["evaluation_id"]
        sess_id = ev["session_id"]
        msg_id = ev["message_id"]
        score = ev["score"]
        is_low = ev["is_low_quality"]
        issues_str = ev["issues"] or "[]"
        suggestion = ev["suggestion"] or "无建议"
        evaluator = ev["evaluator"]
        created = ev["created_at"]
        
        user_q = ev["user_question"] or "（未知提问）"
        ast_a = ev["assistant_answer"] or "（无回答内容）"
        intent_cn = ev["intent_name"] or "其他"
        
        rating = ev["feedback_rating"]
        comment = ev["feedback_comment"]
        
        # 解析问题列表
        try:
            issues_list = json.loads(issues_str)
        except:
            issues_list = []
            
        badge_q = '<span class="quality-badge badge-low">⚠️ 低质量</span>' if is_low == 1 else '<span class="quality-badge badge-high">✅ 高质量</span>'
        badge_ev = f'<span class="quality-badge badge-llm">LLM模型评估</span>' if evaluator == "llm" else f'<span class="quality-badge badge-rules">规则指标评估</span>'
        if evaluator == "rules_feedback":
            badge_ev = f'<span class="quality-badge badge-rules">反馈自动重评估</span>'
            
        feedback_str = "无反馈"
        if rating == "like":
            feedback_str = "👍 赞"
        elif rating == "dislike":
            feedback_str = f"👎 踩 ({comment if comment else '无理由'})"
            
        # 整理 expander 标题
        low_prefix = "⚠️ [低质量] " if is_low == 1 else ""
        card_title = f"{low_prefix}⏱️ {created} | 评分：{score} 分 | 提问：{user_q[:25]}..."
        
        with st.expander(card_title):
            st.markdown(f"**关联会话 ID:** `{sess_id}` | **关联消息 ID:** `{msg_id}`")
            st.markdown(f"**质量指标:** {badge_q} | **评估方法:** {badge_ev} | **用户反馈:** ` {feedback_str} `", unsafe_allow_html=True)
            st.markdown("---")
            
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown(f"**❓ 学生提问 (分类: {intent_cn})：**")
                st.info(user_q)
                
                # 存在问题和优化建议
                st.markdown("**🔍 评估出的缺陷/特征：**")
                if issues_list:
                    for issue in issues_list:
                        st.markdown(f"- ❌ {issue}")
                else:
                    st.markdown("- ✨ 未检测到明显质量缺陷")
                    
                st.markdown("**💡 优化改进意见：**")
                st.success(suggestion)
                
            with c_right:
                st.markdown("**🤖 智能助手答复：**")
                st.code(ast_a, language="markdown")
