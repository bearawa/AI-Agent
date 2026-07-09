# -*- coding: utf-8 -*-
"""
AIZS｜管理后台 —— 知识库批量导入
支持多文件上传、ZIP 压缩包解压导入以及演示知识库一键导入。
"""
import streamlit as st
import pandas as pd
import io
import time
from services.batch_import_service import BatchImportService
from utils.auth_utils import check_admin_login, render_sidebar_nav

# 页面配置
st.set_page_config(
    page_title="批量导入 - AIZS管理后台",
    page_icon="📂",
    layout="wide"
)

# 挂载定制侧边栏导航
render_sidebar_nav()

# 强制进行管理员登录校验，若未登录将停止执行并渲染登录框
check_admin_login()

# 自定义样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
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
    .stat-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-top: 4px solid #5b86e5;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .stat-num {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2b3a4a;
    }
    .stat-lbl {
        font-size: 0.8rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📁 知识库批量导入</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">管理员可以一次性上传多份文档、使用 ZIP 压缩包或一键导入预置演示知识库，实现知识的高效批量入库与去重管理。</p>', unsafe_allow_html=True)

# 实例化批量导入服务
@st.cache_resource
def get_batch_import_service():
    return BatchImportService()

batch_service = get_batch_import_service()

# 定义可选分类
category_options = {
    "招生": "admission",
    "学务": "academic",
    "后勤": "logistics",
    "校园生活": "campus_life",
    "其他": "other"
}

# 统一选择分类
st.markdown("### 🏷️ 1. 选择入库统一分类")
selected_cat_name = st.selectbox("统一指定的业务知识分类（多文件和ZIP包导入将统一标记为此分类，演示导入将使用其本征分类）", list(category_options.keys()), index=0)
selected_cat_id = category_options[selected_cat_name]

st.markdown("### 📤 2. 选择批量导入方式")
tab1, tab2, tab3 = st.tabs(["📄 多文件上传", "📦 ZIP 压缩包导入", "💡 演示文档一键导入"])

results_list = []
triggered = False

with tab1:
    st.markdown("##### 支持一次上传多个 PDF、DOCX、TXT 格式文件")
    uploaded_files = st.file_uploader(
        "请选择多个文件上传",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="multi_file_uploader"
    )
    if uploaded_files:
        if st.button("🚀 开始批量导入所选文件", type="primary", use_container_width=True):
            triggered = True
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            total = len(uploaded_files)
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"正在导入：{file.name} (第 {idx+1}/{total} 个)...")
                # 读取字节
                file_bytes = file.read()
                # 重置流指针以备后用
                file.seek(0)
                
                res = batch_service.import_single_file(file_bytes, file.name, selected_cat_id)
                results_list.append(res)
                
                progress_bar.progress((idx + 1) / total)
                time.sleep(0.1) # 增加微小延迟使进度条过渡更流畅
                
            progress_bar.empty()
            status_text.empty()
            st.success("✅ 文件批量处理完毕！")

with tab2:
    st.markdown("##### 上传一个 .zip 格式压缩包，系统将自动安全解压并过滤导入其中的 PDF、DOCX、TXT 文件")
    uploaded_zip = st.file_uploader(
        "请选择 ZIP 压缩包上传",
        type=["zip"],
        accept_multiple_files=False,
        key="zip_file_uploader"
    )
    if uploaded_zip:
        if st.button("🚀 解压并批量导入 ZIP 知识库", type="primary", use_container_width=True):
            triggered = True
            with st.spinner("正在解压压缩包并执行安全校验中..."):
                zip_bytes = uploaded_zip.read()
                results_list = batch_service.import_zip_file(zip_bytes, selected_cat_id)
            st.success("✅ ZIP 压缩包解压处理完毕！")

with tab3:
    st.markdown("##### 从项目本地 `demo_documents` 目录下自动加载并解析预设的模拟校园咨询手册和规定")
    st.info("💡 **提示**：一键导入演示知识库时，系统将遵循文件本征分类进行划分，不使用上面指定的统一分类。")
    if st.button("🚀 一键导入演示知识库", type="primary", use_container_width=True):
        triggered = True
        with st.spinner("正在扫描演示目录并逐个执行向量导入中..."):
            results_list = batch_service.import_demo_documents()
        st.success("✅ 演示文档导入处理完毕！")

# 展示处理结果和汇总报表
if triggered and results_list:
    report = batch_service.build_import_report(results_list)
    
    st.markdown("### 📊 3. 导入结果汇总报表")
    
    # 汇总卡片展示
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{report['total_files']}</div>
            <div class="stat-lbl">本次处理文件数</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card" style="border-top-color: #2ecc71;">
            <div class="stat-num" style="color: #2ecc71;">{report['success_count']}</div>
            <div class="stat-lbl">成功入库数</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card" style="border-top-color: #f1c40f;">
            <div class="stat-num" style="color: #f1c40f;">{report['skipped_count']}</div>
            <div class="stat-lbl">重复跳过数</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card" style="border-top-color: #e74c3c;">
            <div class="stat-num" style="color: #e74c3c;">{report['failed_count']}</div>
            <div class="stat-lbl">处理失败数</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="stat-card" style="border-top-color: #9b59b6;">
            <div class="stat-num" style="color: #9b59b6;">{report['total_chunks']}</div>
            <div class="stat-lbl">产生切片总数</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    
    # 构建 DataFrame 表格
    df_data = []
    for res in results_list:
        status_cn = "成功"
        if res["status"] == "skipped":
            status_cn = "重复跳过"
        elif res["status"] == "failed":
            status_cn = "失败"
            
        df_data.append({
            "文件名": res["file_name"],
            "文件类型": res["file_type"],
            "文件大小": res["file_size"],
            "设定分类": res["category"],
            "执行状态": status_cn,
            "生成切片数量": res["chunk_count"],
            "异常/跳过原因": res["error_message"] if res["error_message"] else "无"
        })
        
    df = pd.DataFrame(df_data)
    
    # 表格呈现
    st.dataframe(df, use_container_width=True)
    
    # 结果导出下载为 CSV
    csv_io = io.StringIO()
    df.to_csv(csv_io, index=False, encoding='utf-8-sig')
    csv_bytes = csv_io.getvalue().encode('utf-8-sig')
    
    st.download_button(
        label="📥 下载本次批量导入报告 (CSV)",
        data=csv_bytes,
        file_name=f"batch_import_report_{int(time.time())}.csv",
        mime="text/csv",
        use_container_width=True
    )
elif triggered:
    st.warning("⚠️ 没有处理任何有效的文件，请重新检查上传的文件或压缩包。")
