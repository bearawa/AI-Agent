import os
import streamlit as st
from services.rag_service import RAGService
from repositories import sqlite_repository
from utils.logger import logger
from utils.auth_utils import check_admin_login, render_sidebar_nav

# 实例化 RAG 服务
@st.cache_resource
def get_rag_service():
    return RAGService()

rag_service = get_rag_service()

# 页面配置
st.set_page_config(
    page_title="知识库导入 - AIZS",
    page_icon="📚",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# 自定义 premium 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
    .file-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 10px;
        border-left: 5px solid #11998e;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📚 知识库管理与导入</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">支持上传 PDF、DOCX、TXT 格式的校园文件，系统将对文档进行语义切片、向量化并将其录入本地向量知识库。</p>', unsafe_allow_html=True)

# --- 文件上传区域 ---
st.markdown("### 📤 上传新文档")

# 下拉选择分类
category_options = {
    "招生": "admission",
    "学务": "academic",
    "后勤": "logistics",
    "校园生活": "campus_life",
    "其他": "other"
}
selected_cn = st.selectbox("📌 请选择文档所属分类：", list(category_options.keys()), index=4)
selected_en = category_options[selected_cn]

uploaded_file = st.file_uploader(
    "请选择要上传的校园文档 (仅支持 PDF、DOCX、TXT 格式，单个文件限 10MB 左右)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=False
)

if uploaded_file is not None:
    # 提取文件属性
    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue()
    file_size_kb = len(file_bytes) / 1024
    _, ext = os.path.splitext(file_name)
    file_type = ext.lower().lstrip('.')

    # 展示待导入文件卡片
    st.info(f"📋 **待处理文件信息：**\n- **文件名：** {file_name}\n- **分类：** {selected_cn}\n- **类型：** {file_type.upper()} 文件\n- **大小：** {file_size_kb:.2f} KB")

    # 导入按钮触发动作
    if st.button("🚀 开始解析并导入知识库", type="primary"):
        # 显示全局加载动画
        with st.spinner("⏳ 正在进行：文档内容读取 ➡️ 中文分句 ➡️ 中文语义切分 ➡️ 大模型批量向量化 ➡️ ChromaDB 数据持久化..."):
            try:
                # 调用 RAG 服务的导入业务链
                doc_id = rag_service.import_document(file_name, file_bytes, category=selected_en, category_name=selected_cn)
                st.success(f"🎉 导入成功！文档 **{file_name}** 已成功存入知识库，并在 SQLite 关系库和 ChromaDB 向量库中建立双重索引。")
                logger.info(f"前端手动导入文件成功: {file_name}, 分类: {selected_cn}, 生成 doc_id: {doc_id}")
            except ValueError as ve:
                # 处理文件重复上传异常
                st.warning(f"⚠️ **去重提示：** {str(ve)}")
            except Exception as e:
                # 捕获其它异常（如解析损坏文件、百炼 API 连接超时、ChromaDB 写入故障等）
                st.error(f"❌ **导入失败！原因如下：**\n{str(e)}")
                logger.error(f"前端手动导入文件失败: {file_name}, 异常: {e}")

st.markdown("---")

# --- 已入库文档监控列表 ---
st.markdown("### 🔍 知识库已入库文档列表")

documents = sqlite_repository.list_documents()

if not documents:
    st.info("💡 知识库当前空空如也，请在上方上传文档以丰富校园知识储备。")
else:
    # 构建表格数据
    table_data = []
    for doc in documents:
        # 获取物理文件大小
        file_path = doc["file_path"]
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            size_str = f"{size_bytes / 1024:.2f} KB"
        else:
            size_str = "未知（本地文件已清理）"

        # 状态友好展示
        status_map = {
            "completed": "🟢 成功",
            "processing": "🟡 处理中",
            "failed": "🔴 失败"
        }
        status_cn = status_map.get(doc["status"], doc["status"])

        # 错误信息截断展示
        err_msg = doc["error_message"] if doc["error_message"] else "无"
        if len(err_msg) > 40:
            err_msg = err_msg[:40] + "..."

        table_data.append({
            "文档 ID": doc["doc_id"][:8] + "...",
            "文件名": doc["file_name"],
            "文件类型": doc["file_type"].upper(),
            "所属分类": doc.get("category_name", "其他"),
            "物理文件大小": size_str,
            "上传时间": doc["uploaded_at"],
            "处理状态": status_cn,
            "切片数量": doc["chunk_count"],
            "错误记录": err_msg
        })

    # 渲染 DataFrame 视图
    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )
