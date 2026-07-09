# -*- coding: utf-8 -*-
"""
AIZS 管理端 - 系统自检视图
"""
import sys
import os
import streamlit as st
from pathlib import Path
from config import settings
from utils.display_utils import safe_text
from utils.ui_utils import render_page_header, render_empty_state, render_metric_card

def check_item(name, passed, warning=False, detail="", suggestion=""):
    """生成单个自检项结果字典。"""
    if passed:
        status = "✅ 正常"
    elif warning:
        status = "⚠️ 警告"
    else:
        status = "❌ 异常"
    return {
        "检查项": name,
        "状态": status,
        "详情": detail,
        "修复建议": suggestion
    }

def render():
    render_page_header(
        "🔧 AIZS 系统自检",
        "管理员可在此页面检查系统各组件的运行状态，排查常见配置问题。"
    )

    results = []

    # 1. 项目根目录检查
    base_dir = str(settings.BASE_DIR)
    has_jcd = "JCD" in base_dir.upper() and "AIZS" not in base_dir.upper()
    results.append(check_item(
        "项目根目录",
        not has_jcd,
        warning=has_jcd,
        detail=base_dir,
        suggestion="请确认是否已将项目目录重命名为 D:\\AIZS" if has_jcd else ""
    ))

    # 2. Python 版本
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    results.append(check_item(
        "Python 版本",
        py_ok,
        warning=not py_ok,
        detail=py_ver,
        suggestion="推荐使用 Python 3.11+，当前版本可能不兼容部分功能" if not py_ok else ""
    ))

    # 3. DASHSCOPE_API_KEY
    key_configured = bool(settings.DASHSCOPE_API_KEY)
    results.append(check_item(
        "DASHSCOPE_API_KEY",
        key_configured,
        warning=not key_configured,
        detail=settings.DASHSCOPE_API_KEY[:6] + "***" if key_configured else "未配置",
        suggestion="请在 .env 文件中填写有效的 API Key" if not key_configured else ""
    ))

    # 4. BASE_URL
    base_url_configured = bool(settings.DASHSCOPE_BASE_URL)
    results.append(check_item(
        "BASE_URL",
        base_url_configured,
        warning=not base_url_configured,
        detail=safe_text(settings.DASHSCOPE_BASE_URL),
        suggestion="请在 .env 文件中填写正确的 API Base URL" if not base_url_configured else ""
    ))

    # 5. SQLite 数据库
    db_path = settings.SQLITE_PATH
    db_exists = os.path.exists(db_path)
    results.append(check_item(
        "SQLite 数据库",
        db_exists,
        warning=not db_exists,
        detail=db_path,
        suggestion="运行 `python scripts/reset_demo_data.py` 初始化数据库" if not db_exists else ""
    ))

    # 6. ChromaDB 向量库
    chroma_path = settings.CHROMA_DIR
    chroma_exists = os.path.exists(chroma_path)
    results.append(check_item(
        "ChromaDB 向量库",
        chroma_exists,
        warning=not chroma_exists,
        detail=chroma_path,
        suggestion="首次使用会自动创建，或运行 `python scripts/reset_demo_data.py` 初始化" if not chroma_exists else ""
    ))

    # 7. demo_documents 演示文档
    demo_docs_path = str(settings.BASE_DIR / "demo_documents")
    demo_docs_exist = os.path.exists(demo_docs_path) and len(os.listdir(demo_docs_path)) > 0
    results.append(check_item(
        "demo_documents 演示文档",
        demo_docs_exist,
        warning=not demo_docs_exist,
        detail=f"{demo_docs_path} ({len(os.listdir(demo_docs_path)) if demo_docs_exist else 0} 个文件)",
        suggestion="从 demo_documents 目录复制示例文档到 data/raw_documents" if not demo_docs_exist else ""
    ))

    # 8. 天气工具模式（可选功能）
    weather_mode = os.getenv("WEATHER_TOOL_MODE", "mock")
    weather_ok = weather_mode in ["mock", "api"]
    results.append(check_item(
        "天气工具模式",
        weather_ok,
        warning=not weather_ok,
        detail=f"当前模式: {weather_mode}",
        suggestion="请在 .env 中设置 WEATHER_TOOL_MODE=mock（模拟）或 api（真实API）" if not weather_ok else ""
    ))

    # 9. 第三方库
    required_libs = ["openai", "pandas", "plotly", "chromadb", "streamlit"]
    missing_libs = []
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    libs_ok = len(missing_libs) == 0
    results.append(check_item(
        "第三方库依赖",
        libs_ok,
        warning=not libs_ok,
        detail=f"已安装 {len(required_libs) - len(missing_libs)}/{len(required_libs)} 个核心库",
        suggestion=f"运行 `pip install {' '.join(missing_libs)}` 安装缺失的库" if not libs_ok else ""
    ))

    # 10. 数据目录
    data_dirs = [
        ("data/raw_documents", settings.UPLOAD_DIR),
        ("data/chroma_db", settings.CHROMA_DIR),
        ("logs", os.path.dirname(settings.LOG_FILE))
    ]
    all_dirs_ok = True
    dir_details = []
    for name, path in data_dirs:
        exists = os.path.exists(path)
        if not exists:
            all_dirs_ok = False
        dir_details.append(f"{name}: {'✅' if exists else '❌'}")
    results.append(check_item(
        "数据目录结构",
        all_dirs_ok,
        warning=not all_dirs_ok,
        detail="\n".join(dir_details),
        suggestion="手动创建缺失的目录，或运行 `python scripts/reset_demo_data.py`" if not all_dirs_ok else ""
    ))

    # 显示检查结果
    st.markdown("###  自检结果汇总")
    
    if any(r["状态"].startswith("❌") for r in results):
        st.error("️ 发现异常项，请根据下方的修复建议进行排查。")
    elif any(r["状态"].startswith("⚠️") for r in results):
        st.warning("⚡ 发现警告项，建议优化配置以获得最佳体验。")
    else:
        st.success("✅ 所有检查项均通过，系统运行正常！")

    # 以表格形式展示
    df_data = []
    for r in results:
        df_data.append({
            "检查项": r["检查项"],
            "状态": r["状态"],
            "详情": r["详情"],
            "修复建议": r["修复建议"]
        })
    
    import pandas as pd
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 模型连通性测试区域
    if key_configured:
        st.markdown("---")
        st.markdown("### 🔌 模型连通性测试")
        st.caption("⚡ 点击按钮测试大模型和向量模型的实际连通性，该操作会发送真实 API 请求。")

        col_m1, col_m2 = st.columns(2)

        with col_m1:
            if st.button("🧪 测试 qwen-plus 连通性", use_container_width=True):
                if not key_configured:
                    st.error("❌ 未配置 API Key，无法进行连通性测试。请在 .env 中填写 DASHSCOPE_API_KEY。")
                else:
                    with st.spinner("正在测试 qwen-plus 连通性..."):
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
                            response = client.chat.completions.create(
                                model=settings.CHAT_MODEL,
                                messages=[{"role": "user", "content": "你好，请回复'连通性测试通过'"}],
                                temperature=0.1,
                                max_tokens=20
                            )
                            reply = response.choices[0].message.content.strip()
                            st.success(f"✅ qwen-plus 连通性正常！回复: {reply}")
                        except Exception as e:
                            st.error(f"❌ qwen-plus 连通性异常: {e}")

        with col_m2:
            if st.button("🧪 测试 text-embedding-v3 连通性", use_container_width=True):
                if not key_configured:
                    st.error(" 未配置 API Key，无法进行连通性测试。请在 .env 中填写 DASHSCOPE_API_KEY。")
                else:
                    with st.spinner("正在测试 text-embedding-v3 连通性..."):
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=settings.DASHSCOPE_BASE_URL)
                            response = client.embeddings.create(
                                model=settings.EMBEDDING_MODEL,
                                input=["连通性测试"]
                            )
                            dim = len(response.data[0].embedding)
                            st.success(f"✅ text-embedding-v3 连通性正常！向量维度: {dim}")
                        except Exception as e:
                            st.error(f"❌ text-embedding-v3 连通性异常: {e}")
    else:
        st.info("💡 未配置 API Key，跳过模型连通性测试。请在 `.env` 中填写 `DASHSCOPE_API_KEY` 后刷新页面。")
