# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 知识库导入与管理中心
将原"单文件导入"、"批量导入"、"知识库管理"三个独立页面整合为统一的管理中心。

功能分区（使用 Tab 布局）：
  Tab 1 - 导入知识库：多文件上传 / ZIP压缩包 / 演示文档一键导入
  Tab 2 - 已入库文档：列表展示、分类筛选、批量选择、批量删除
  Tab 3 - 清理失败记录：一键清理所有失败导入记录及残留资源
重构版：使用主题管理器和组件库提供企业级用户体验。
"""
import io
import os
import time
import streamlit as st
import pandas as pd
from services.batch_import_service import BatchImportService
from services.knowledge_admin_service import KnowledgeAdminService
from repositories import sqlite_repository
from utils.ui_utils import render_page_header, render_empty_state
from themes.theme_manager import theme_manager

# 获取主题配置
theme = theme_manager.current_theme
colors = theme["colors"]
spacing = theme["spacing"]
typography = theme["typography"]
radius = theme["radius"]

# ─────────────────────────────────────────────────────────────────
# 缓存服务实例（避免每次重渲染都重新初始化 ChromaDB 等资源）
# ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_batch_service():
    return BatchImportService()

@st.cache_resource
def get_admin_service():
    return KnowledgeAdminService()

# ─────────────────────────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────────────────────────
CATEGORY_OPTIONS = {
    "自动识别": "auto",
    "通用资料": "general",
    "招生": "admission",
    "学务": "academic",
    "后勤": "logistics",
    "校园生活": "campus_life",
    "其他": "other"
}

STATUS_MAP = {
    "completed": "🟢 成功",
    "processing": "🟡 处理中",
    "failed": "🔴 失败",
    "error": "🔴 错误",
    "import_failed": "🔴 导入失败",
    "processing_failed": "🔴 处理失败",
}

FAILED_STATUSES = {"failed", "error", "import_failed", "processing_failed"}


def _render_stat_card(value, label, color=None):
    """渲染统计卡片。"""
    bg_color = color or colors["primary"]
    st.markdown(f"""
    <div style="background:{colors['bg_card']};border-radius:{radius['radius_lg']};padding:{spacing['spacing_base']};
                border-top:4px solid {bg_color};text-align:center;
                box-shadow:{colors['shadow_card']};">
        <div style="font-size:1.8rem;font-weight:{typography['font_weight_bold']};color:{colors['text_primary']};">{value}</div>
        <div style="font-size:{typography['font_size_xs']};color:{colors['text_tertiary']};margin-top:{spacing['spacing_xxs']};">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def _build_import_result_df(results_list):
    """将批量导入结果列表转换为 DataFrame。"""
    df_data = []
    for res in results_list:
        raw_status = res.get("status", "failed")
        if raw_status == "success":
            status_cn = "✅ 成功"
        elif raw_status == "skipped":
            status_cn = "⏭️ 重复跳过"
        else:
            status_cn = "❌ 失败"

        df_data.append({
            "文件名": res.get("file_name", ""),
            "文件类型": res.get("file_type", ""),
            "文件大小": res.get("file_size", ""),
            "分类": res.get("category", ""),
            "导入状态": status_cn,
            "切片数量": res.get("chunk_count", 0),
            "错误原因": res.get("error_message", "") or "无"
        })
    return pd.DataFrame(df_data)


# ─────────────────────────────────────────────────────────────────
# Tab 1：导入知识库
# ─────────────────────────────────────────────────────────────────
def _render_import_tab(batch_service: BatchImportService):
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🏷️ 1. 选择入库统一分类</h3>", unsafe_allow_html=True)
    st.caption(f"<span style='color:{colors['text_tertiary']};'>分类仅用于知识库管理和检索排序辅助，不会限制用户从全知识库中查找答案。</span>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:{colors['info']}15;border-left:4px solid {colors['info']};padding:{spacing['spacing_sm']} {spacing['spacing_base']};border-radius:{radius['radius_base']};color:{colors['text_secondary']};font-size:{typography['font_size_sm']};">
            💡 <strong>推荐提示</strong>：建议优先选择"通用资料"或"自动识别"。即使选择了具体分类，系统回答问题时也会进行全知识库检索，避免因为分类错误漏掉真实资料。
        </div>
    """, unsafe_allow_html=True)
    selected_cat_name = st.selectbox(
        "业务知识分类",
        list(CATEGORY_OPTIONS.keys()),
        index=0,
        key="kc_cat_select"
    )
    selected_cat_id = CATEGORY_OPTIONS[selected_cat_name]

    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📤 2. 选择导入方式</h3>", unsafe_allow_html=True)
    tab_multi, tab_zip, tab_demo = st.tabs(["📄 多文件上传（含单文件）", "📦 ZIP 压缩包", "💡 演示文档一键导入"])

    # ── Tab: 多文件上传 ──
    with tab_multi:
        st.markdown(
            "支持一次上传 **一个或多个** PDF、DOCX、TXT 文件。"
            "上传单个文件即等同于原「单文件导入」功能。"
        )
        uploaded_files = st.file_uploader(
            "选择文件（可多选）",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="kc_multi_uploader"
        )
        if uploaded_files:
            st.markdown(f"已选择 **{len(uploaded_files)}** 个文件，点击下方按钮开始导入。")
            if st.button("🚀 开始导入所选文件", type="primary", use_container_width=True, key="kc_multi_btn"):
                progress_bar = st.progress(0.0)
                status_placeholder = st.empty()
                results_list = []
                total = len(uploaded_files)
                for idx, file in enumerate(uploaded_files):
                    status_placeholder.text(f"正在导入：{file.name} ({idx+1}/{total})...")
                    file_bytes = file.read()
                    res = batch_service.import_single_file(file_bytes, file.name, selected_cat_id)
                    results_list.append(res)
                    progress_bar.progress((idx + 1) / total)
                    time.sleep(0.05)
                progress_bar.empty()
                status_placeholder.empty()
                st.session_state["kc_import_results"] = results_list
                st.markdown("✅ 文件处理完毕！请查看下方汇总报表。")
                st.rerun()

    # ── Tab: ZIP 导入 ──
    with tab_zip:
        st.markdown(
            "上传一个 `.zip` 压缩包，系统将自动解压并导入其中的 PDF、DOCX、TXT 文件，"
            "其余格式将被跳过。解压过程已启用 **Zip Slip 路径穿越攻击防御**。"
        )
        uploaded_zip = st.file_uploader(
            "选择 ZIP 压缩包",
            type=["zip"],
            accept_multiple_files=False,
            key="kc_zip_uploader"
        )
        if uploaded_zip:
            if st.button("🚀 解压并批量导入", type="primary", use_container_width=True, key="kc_zip_btn"):
                with st.spinner("正在解压并安全检验压缩包内容..."):
                    try:
                        zip_bytes = uploaded_zip.read()
                        results_list = batch_service.import_zip_file(zip_bytes, selected_cat_id)
                        st.session_state["kc_import_results"] = results_list
                        st.markdown("✅ ZIP 压缩包处理完毕！")
                    except Exception as e:
                        st.markdown(f"❌ ZIP 导入出错：{e}")
                st.rerun()

    # ── Tab: 演示文档 ──
    with tab_demo:
        st.markdown(
            "从项目 `demo_documents/` 目录一键导入预置演示知识库，"
            "系统将使用文件本征分类（不受上方分类选择影响）。"
            "已导入文件将根据 **SHA-256 哈希** 自动跳过。"
        )
        st.markdown("💡 演示导入使用预定义的分类映射，不受上方分类选择框控制。")
        if st.button("🚀 一键导入演示知识库", type="primary", use_container_width=True, key="kc_demo_btn"):
            with st.spinner("正在扫描演示目录并逐个向量化入库..."):
                try:
                    results_list = batch_service.import_demo_documents()
                    st.session_state["kc_import_results"] = results_list
                    st.markdown("✅ 演示文档导入处理完毕！")
                except Exception as e:
                    st.markdown(f"❌ 演示数据导入失败：{e}")
            st.rerun()

    # ── 导入结果汇总 ──
    if st.session_state.get("kc_import_results"):
        results_list = st.session_state["kc_import_results"]
        report = batch_service.build_import_report(results_list)

        st.markdown("---")
        st.markdown(f"<h3 style='color:{colors['text_primary']};'>📊 3. 本次导入结果汇总</h3>", unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5, gap="small")
        with c1: _render_stat_card(report["total_files"], "处理文件数")
        with c2: _render_stat_card(report["success_count"], "成功入库数", colors["success"])
        with c3: _render_stat_card(report["skipped_count"], "重复跳过数", colors["warning"])
        with c4: _render_stat_card(report["failed_count"], "处理失败数", colors["error"])
        with c5: _render_stat_card(report["total_chunks"], "产生切片数", colors["primary"])

        st.write("")
        df = _build_import_result_df(results_list)
        st.dataframe(df, use_container_width=True)

        # 导出 CSV（utf-8-sig 避免 Excel 乱码）
        csv_io = io.StringIO()
        df.to_csv(csv_io, index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 下载本次导入报告（CSV）",
            data=csv_io.getvalue().encode("utf-8-sig"),
            file_name=f"知识库导入报告_{int(time.time())}.csv",
            mime="text/csv",
            use_container_width=True,
            key="kc_download_csv"
        )

        if st.button("🧹 清除本次结果缓存", use_container_width=True, key="kc_clear_cache"):
            st.session_state["kc_import_results"] = None
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# Tab 2：已入库文档（含批量删除）
# ─────────────────────────────────────────────────────────────────
def _render_manage_tab(admin_service: KnowledgeAdminService):
    documents = sqlite_repository.list_documents()

    # 统计概览
    total = len(documents)
    completed = sum(1 for d in documents if d.get("status") == "completed")
    failed = sum(1 for d in documents if d.get("status") in FAILED_STATUSES)

    col1, col2, col3 = st.columns(3, gap="small")
    with col1: st.metric("总入库文档数", f"{total} 篇")
    with col2: st.metric("正常运行数", f"{completed} 篇")
    with col3: st.metric("失败记录数", f"{failed} 篇",
                         delta="需清理" if failed > 0 else "一切正常",
                         delta_color="inverse" if failed > 0 else "normal")

    if not documents:
        render_empty_state(
            title="暂无知识库文档",
            description="请前往「导入知识库」标签页先导入资料。",
            icon="📂"
        )
        return

    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>📂 文档列表与批量操作</h3>", unsafe_allow_html=True)

    # 分类筛选
    categories = ["全部", "通用资料", "招生", "学务", "后勤", "校园生活", "其他"]
    col_filter, col_status_filter = st.columns([1, 1], gap="small")
    with col_filter:
        selected_filter = st.selectbox("🔍 按分类筛选", categories, key="kc_cat_filter")
    with col_status_filter:
        status_filter = st.selectbox("🔍 按状态筛选", ["全部", "成功", "处理中", "失败"], key="kc_status_filter")

    # 格式化和防崩溃字段兜底
    formatted_docs = []
    for doc in documents:
        raw_status = doc.get("status") or "未知状态"
        status_cn = STATUS_MAP.get(raw_status, raw_status)
        uploaded_at = doc.get("uploaded_at") or "未知时间"
        
        # 文件大小
        file_path = doc.get("file_path", "")
        if file_path and os.path.exists(file_path):
            size_str = f"{os.path.getsize(file_path) / 1024:.1f} KB"
        else:
            size_str = "文件已清理"

        formatted_docs.append({
            "doc_id": doc.get("doc_id", ""),
            "file_name": doc.get("file_name") or "未命名文档",
            "file_type": (doc.get("file_type") or "UNKNOWN").upper(),
            "category": doc.get("category") or "other",
            "category_name": doc.get("category_name") or "未分类",
            "status": status_cn,
            "raw_status": raw_status,
            "uploaded_at": uploaded_at,
            "chunk_count": doc.get("chunk_count") or 0,
            "file_size": size_str,
            "error_message": doc.get("error_message") or ""
        })

    # 筛选逻辑
    filtered_docs = []
    for doc in formatted_docs:
        cat_name = doc["category_name"]
        if selected_filter != "全部" and cat_name != selected_filter:
            continue
        
        raw_status = doc["raw_status"]
        if status_filter == "成功" and raw_status != "completed":
            continue
        if status_filter == "处理中" and raw_status != "processing":
            continue
        if status_filter == "失败" and raw_status not in FAILED_STATUSES:
            continue
        filtered_docs.append(doc)

    if not filtered_docs:
        render_empty_state(
            title="当前筛选条件下暂无文档",
            description="请尝试调整筛选条件或切换分类查看其他文档。",
            icon="🔍"
        )
        return

    # 批量选择控制初始化
    if "selected_doc_ids" not in st.session_state:
        st.session_state["selected_doc_ids"] = set()
    if "confirm_batch_delete" not in st.session_state:
        st.session_state["confirm_batch_delete"] = False

    # 自动对 selected_doc_ids 进行库内有效性过滤（移除已被外部删除的 doc_id）
    db_doc_ids = {doc["doc_id"] for doc in formatted_docs}
    st.session_state["selected_doc_ids"] = st.session_state["selected_doc_ids"] & db_doc_ids

    # 计算当前筛选出来的所有文档 ID 集合
    current_doc_ids = {doc["doc_id"] for doc in filtered_docs}

    col_all, col_none, col_ref = st.columns(3, gap="small")
    with col_all:
        if st.button("☑️ 全选当前页/列表", use_container_width=True, key="kc_select_all_list"):
            st.session_state["selected_doc_ids"].update(current_doc_ids)
            if "knowledge_docs_editor" in st.session_state:
                del st.session_state["knowledge_docs_editor"]
            st.rerun()
    with col_none:
        if st.button("⬜ 取消全选", use_container_width=True, key="kc_deselect_all_list"):
            st.session_state["selected_doc_ids"] = set()
            st.session_state["confirm_batch_delete"] = False
            if "knowledge_docs_editor" in st.session_state:
                del st.session_state["knowledge_docs_editor"]
            st.rerun()
    with col_ref:
        if st.button("🔄 刷新列表", use_container_width=True, key="kc_refresh_list"):
            st.rerun()

    # 转换为 DataFrame 并加上选择列
    df = pd.DataFrame(filtered_docs)
    df["selected"] = df["doc_id"].apply(
        lambda d_id: d_id in st.session_state["selected_doc_ids"]
    )

    # 调整排布，将 selected 排最前
    cols_order = ["selected", "file_name", "category_name", "status", "uploaded_at", "chunk_count", "file_size", "error_message", "doc_id"]
    df = df[cols_order]

    edited_df = st.data_editor(
        df,
        key="knowledge_docs_editor",
        hide_index=True,
        use_container_width=True,
        column_config={
            "selected": st.column_config.CheckboxColumn("选择", default=False),
            "file_name": st.column_config.TextColumn("文件名"),
            "category_name": st.column_config.TextColumn("分类"),
            "status": st.column_config.TextColumn("状态"),
            "uploaded_at": st.column_config.TextColumn("上传时间"),
            "chunk_count": st.column_config.NumberColumn("切片数"),
            "file_size": st.column_config.TextColumn("文件大小"),
            "error_message": st.column_config.TextColumn("错误原因"),
            "doc_id": st.column_config.TextColumn("文档ID")
        },
        disabled=[
            "doc_id",
            "file_name",
            "category_name",
            "status",
            "uploaded_at",
            "chunk_count",
            "file_size",
            "error_message",
        ],
    )

    # 提取被用户修改后当前的最新勾选状态
    newly_selected = set(edited_df.loc[edited_df["selected"] == True, "doc_id"].tolist())
    newly_deselected = current_doc_ids - newly_selected

    # 合并写回
    st.session_state["selected_doc_ids"].update(newly_selected)
    st.session_state["selected_doc_ids"].difference_update(newly_deselected)

    # ── 批量删除区域 ──
    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🗑️ 批量操作已选文档</h3>", unsafe_allow_html=True)

    selected_count = len(st.session_state["selected_doc_ids"])
    st.write(f"当前已选择 **{selected_count}** 个文档。")

    if selected_count == 0:
        st.markdown("请先在上方表格中勾选要操作的文档。")
    else:
        if st.button("🗑️ 批量删除已选文档", type="secondary", use_container_width=True, key="kc_batch_del_btn"):
            st.session_state["confirm_batch_delete"] = True

        if st.session_state.get("confirm_batch_delete", False):
            st.markdown(
                f"""
                <div style="background:{colors['error']}15;border-left:4px solid {colors['error']};padding:{spacing['spacing_base']};border-radius:{radius['radius_base']};">
                    ⚠️ <strong>高危操作确认</strong><br/><br/>
                    该操作将删除选中的 <strong>{selected_count}</strong> 个文档，
                    包括其 SQLite 记录、ChromaDB 向量切片、来源引用和上传原文件，<strong>且不可撤销</strong>。<br/>
                    *(安全提示：系统将自动保留 demo_documents 目录下的原始演示资料，仅清理其库内切片索引)*
                </div>
                """,
                unsafe_allow_html=True
            )
            confirmed = st.checkbox(
                "✅ 我确认删除选中的知识库文档，且了解此操作无法撤销",
                key="kc_batch_del_confirm_chk"
            )
            col_exec, col_cancel = st.columns([1, 4], gap="small")
            with col_exec:
                if st.button("🔥 确认批量删除", type="primary", key="kc_batch_del_exec"):
                    if not confirmed:
                        st.markdown("请先勾选上方的确认复选框。")
                    else:
                        with st.spinner("正在执行批量删除..."):
                            batch_result = admin_service.delete_documents_batch(list(st.session_state["selected_doc_ids"]))

                        deleted = batch_result["deleted"]
                        failed_cnt = batch_result["failed"]

                        if failed_cnt == 0:
                            st.markdown(f"✅ 已成功删除 {deleted} 个文档。")
                        else:
                            st.markdown(f"⚠️ 部分文档删除失败：成功 {deleted} 个，失败 {failed_cnt} 个，请查看下方明细。")

                        # 展示删除结果明细
                        result_data = []
                        for item in batch_result["items"]:
                            result_data.append({
                                "文件名": item.get("file_name", "未知"),
                                "删除结果": "✅ 成功" if item.get("status") == "deleted" else "❌ 失败",
                                "说明": item.get("message", "成功")
                            })
                        st.dataframe(pd.DataFrame(result_data), use_container_width=True)

                        # 清除已选中状态与删除缓存
                        st.session_state["selected_doc_ids"] = set()
                        st.session_state["confirm_batch_delete"] = False
                        if "knowledge_docs_editor" in st.session_state:
                            del st.session_state["knowledge_docs_editor"]
                        time.sleep(1.0)
                        st.rerun()

            with col_cancel:
                if st.button("取消", key="kc_batch_del_cancel"):
                    st.session_state["confirm_batch_delete"] = False
                    st.rerun()


# ─────────────────────────────────────────────────────────────────
# Tab 3：清理失败记录
# ─────────────────────────────────────────────────────────────────
def _render_cleanup_tab(admin_service: KnowledgeAdminService):
    failed_docs = sqlite_repository.list_failed_documents()

    if not failed_docs:
        st.markdown(f"""
            <div style="background:{colors['success']}15;border-left:4px solid {colors['success']};padding:{spacing['spacing_base']};border-radius:{radius['radius_base']};color:{colors['text_secondary']};font-size:{typography['font_size_sm']};">
                ✅ 当前没有失败导入记录，知识库状态良好！
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(
        f"检测到 **{len(failed_docs)}** 条失败导入记录。"
        "可一键清理这些记录及其残留的 ChromaDB 向量和磁盘文件。"
    )

    # 展示失败记录列表（只读预览）
    st.markdown(f"<h4 style='color:{colors['text_secondary']};'>当前失败记录预览</h4>", unsafe_allow_html=True)
    preview_data = []
    for doc in failed_docs:
        preview_data.append({
            "文件名": doc.get("file_name", ""),
            "分类": doc.get("category_name") or "未分类",
            "状态": STATUS_MAP.get(doc.get("status", "failed"), "失败"),
            "上传时间": doc.get("uploaded_at", ""),
            "错误信息": (doc.get("error_message") or "无")[:80]
        })
    st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

    st.markdown("---")
    st.markdown(f"<h3 style='color:{colors['text_primary']};'>🧹 一键清理失败导入记录</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background:{colors['info']}15;border-left:4px solid {colors['info']};padding:{spacing['spacing_base']};border-radius:{radius['radius_base']};color:{colors['text_secondary']};font-size:{typography['font_size_sm']};">
            <strong>清理范围</strong>：失败状态的 documents 记录、ChromaDB 残留向量、message_sources 脏引用、磁盘残留文件。<br/><br/>
            <strong>绝对不会清理</strong>：已成功导入的文档、demo_documents 原始演示资料、数据库本身。
        </div>
    """, unsafe_allow_html=True)

    confirmed_clean = st.checkbox(
        "✅ 我确认清理所有失败导入记录（不会影响已成功入库的文档）",
        key="kc_clean_confirm_chk"
    )

    if st.button("🧹 执行清理", type="primary", use_container_width=True, key="kc_clean_exec_btn"):
        if not confirmed_clean:
            st.markdown("请先勾选上方的确认复选框。")
        else:
            with st.spinner("正在清理失败记录及残留资源..."):
                clean_result = admin_service.clear_failed_documents()

            cleared = clean_result["cleared"]
            failed_cnt = clean_result["failed"]

            if failed_cnt == 0:
                st.markdown(f"✅ 清理完成！共清理 {cleared} 条失败记录。")
            else:
                st.markdown(f"⚠️ 清理部分完成：已清理 {cleared} 条，{failed_cnt} 条清理失败，请查看明细。")

            # 展示清理结果明细
            if clean_result["items"]:
                result_data = []
                for item in clean_result["items"]:
                    result_data.append({
                        "文件名": item["file_name"],
                        "原状态": item["original_status"],
                        "清理结果": "✅ 已清理" if item["result"] == "cleared" else "❌ 失败",
                        "说明": item["message"]
                    })
                st.dataframe(pd.DataFrame(result_data), use_container_width=True)

            st.session_state["kc_clean_confirm_chk"] = False
            time.sleep(0.5)
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# 主渲染入口
# ─────────────────────────────────────────────────────────────────
def render():
    batch_service = get_batch_service()
    admin_service = get_admin_service()

    # 初始化 session state
    if "kc_import_results" not in st.session_state:
        st.session_state["kc_import_results"] = None
    if "kc_selected_ids" not in st.session_state:
        st.session_state["kc_selected_ids"] = set()
    if "kc_show_batch_confirm" not in st.session_state:
        st.session_state["kc_show_batch_confirm"] = False

    # 页面标题
    render_page_header(
        "📚 AIZS 知识库导入与管理",
        "统一管理校园知识库的导入、查看和清理操作。上传单个文件即为单文件导入，上传多个文件即为批量导入，同时支持 ZIP 压缩包和演示文档一键入库。"
    )

    # 三大功能 Tab
    tab_import, tab_manage, tab_cleanup = st.tabs([
        "📤 导入知识库",
        "📂 已入库文档",
        "🧹 清理失败记录"
    ])

    with tab_import:
        _render_import_tab(batch_service)

    with tab_manage:
        _render_manage_tab(admin_service)

    with tab_cleanup:
        _render_cleanup_tab(admin_service)
