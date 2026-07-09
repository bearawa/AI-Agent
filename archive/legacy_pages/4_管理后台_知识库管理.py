import streamlit as st
import os
from services.knowledge_admin_service import KnowledgeAdminService
from repositories import sqlite_repository
from utils.logger import logger
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav

# 初始化管理服务
@st.cache_resource
def get_admin_service():
    return KnowledgeAdminService()

admin_service = get_admin_service()

# 页面基本设置
st.set_page_config(
    page_title="知识库管理 - AIZS 管理后台",
    page_icon="🛠️",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# 注入自定义 Premium 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
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
    .doc-row {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border-left: 5px solid #3498db;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .doc-category {
        background-color: #e8f4fd;
        color: #2980b9;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🛠️ 知识库管理后台</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">在这里，管理员可以查看并管理系统中已入库的全部知识文档，支持按分类筛选、查看切片详情以及强一致性的级联删除操作。</p>', unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：知识库管理")
render_logout_button()

# 1. 查询数据库中所有的文档列表
documents = sqlite_repository.list_documents()

# 2. 分类统计与概览卡片
st.markdown("### 📊 知识储备概览")
total_docs = len(documents)
completed_docs = len([d for d in documents if d["status"] == "completed"])
failed_docs = len([d for d in documents if d["status"] == "failed"])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("总入库文档数", f"{total_docs} 篇")
with col2:
    st.metric("正常运行数", f"{completed_docs} 篇", delta="运行中")
with col3:
    st.metric("导入失败数", f"{failed_docs} 篇", delta="-需清理" if failed_docs > 0 else "一切正常", delta_color="inverse" if failed_docs > 0 else "normal")

st.markdown("---")

# 3. 文档筛选与列表展示
st.markdown("### 📂 已入库文档明细")

if not documents:
    st.info("💡 系统知识库中暂无任何文档，请先前往 [知识库导入] 页面上传文件。")
else:
    # 类别筛选过滤
    categories = ["全部", "招生", "学务", "后勤", "校园生活", "其他"]
    selected_filter = st.selectbox("🔍 按文档分类筛选：", categories)

    filtered_docs = []
    for doc in documents:
        # 进行分类筛选
        cat_name = doc.get("category_name", "其他")
        if selected_filter == "全部" or cat_name == selected_filter:
            filtered_docs.append(doc)

    if not filtered_docs:
        st.warning(f"没有找到属于 '{selected_filter}' 分类的文档。")
    else:
        # 表头展示
        col_header = st.columns([3, 1.5, 1.5, 2, 1.5, 1.5])
        with col_header[0]: st.markdown("**文件名**")
        with col_header[1]: st.markdown("**分类**")
        with col_header[2]: st.markdown("**切片数**")
        with col_header[3]: st.markdown("**上传时间**")
        with col_header[4]: st.markdown("**处理状态**")
        with col_header[5]: st.markdown("**操作**")
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 12px;'/>", unsafe_allow_html=True)

        # 循环渲染每一行
        for idx, doc in enumerate(filtered_docs):
            doc_id = doc["doc_id"]
            file_name = doc["file_name"]
            cat_name = doc.get("category_name", "其他")
            chunk_count = doc["chunk_count"]
            uploaded_at = doc["uploaded_at"]
            status = doc["status"]

            # 处理状态显示
            status_map = {
                "completed": "🟢 成功",
                "processing": "🟡 处理中",
                "failed": "🔴 失败"
            }
            status_cn = status_map.get(status, status)

            # 每行渲染为 Streamlit Columns
            col_row = st.columns([3, 1.5, 1.5, 2, 1.5, 1.5])
            
            with col_row[0]:
                st.markdown(f"**{file_name}**")
            with col_row[1]:
                st.markdown(f"<span class='doc-category'>{cat_name}</span>", unsafe_allow_html=True)
            with col_row[2]:
                st.markdown(f"`{chunk_count} 个`")
            with col_row[3]:
                st.markdown(f"<small>{uploaded_at}</small>", unsafe_allow_html=True)
            with col_row[4]:
                st.markdown(status_cn)
            with col_row[5]:
                # 删除按钮
                if st.button("🗑️ 删除", key=f"del_btn_{doc_id}_{idx}", type="secondary"):
                    # 弹出二次确认框，利用 session state 或简单的 streamlit 弹窗
                    st.session_state[f"confirm_delete_{doc_id}"] = True
            
            # 处理二次确认状态
            if st.session_state.get(f"confirm_delete_{doc_id}", False):
                st.error(f"⚠️ 您确定要删除文档 **{file_name}** 吗？此操作将同步彻底删除 ChromaDB 向量、引用记录和本地磁盘物理文件！")
                c1, c2 = st.columns([1, 8])
                with c1:
                    if st.button("确定", key=f"yes_del_{doc_id}", type="primary"):
                        # 执行删除
                        success = admin_service.delete_document(doc_id)
                        if success:
                            st.success(f"成功删除文档: {file_name}")
                            st.session_state[f"confirm_delete_{doc_id}"] = False
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("删除文档失败，请检查日志。")
                with c2:
                    if st.button("取消", key=f"no_del_{doc_id}"):
                        st.session_state[f"confirm_delete_{doc_id}"] = False
                        st.rerun()
            
            # 画一条灰色的细线分隔行
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px; border-top: 1px solid #f1f2f6;'/>", unsafe_allow_html=True)
