# -*- coding: utf-8 -*-
import sys
import os
import streamlit as st
from pathlib import Path
from utils.auth_utils import check_admin_login, render_logout_button, render_sidebar_nav

# 页面配置
st.set_page_config(
    page_title="系统自检 - AIZS 管理后台",
    page_icon="🔧",
    layout="wide"
)

# 挂载定制侧边栏导航和登录拦截校验
render_sidebar_nav()
check_admin_login()


# 样式
st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f2027 0%, #2c5364 100%);
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
    .check-ok { color: #27ae60; font-weight: bold; }
    .check-warn { color: #f39c12; font-weight: bold; }
    .check-fail { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🔧 AIZS｜系统自检</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">管理员可在此页面检查系统各组件的运行状态，排查常见配置问题。</p>', unsafe_allow_html=True)

# 侧边栏
st.sidebar.markdown("### ⚙️ AIZS 管理后台")
st.sidebar.info("当前模块：系统自检")
render_logout_button()


def check_item(name, passed, warning=False, detail="", suggestion=""):
    """生成检查结果字典"""
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


results = []

# 1. 项目根目录检查
from config import settings
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
api_key = settings.DASHSCOPE_API_KEY
key_configured = bool(api_key and api_key.strip())
results.append(check_item(
    "DASHSCOPE_API_KEY",
    key_configured,
    detail=f"已配置（{api_key[:4]}****{api_key[-4:]}）" if key_configured else "未配置",
    suggestion="请在 .env 中填写 DASHSCOPE_API_KEY" if not key_configured else ""
))

# 4. DASHSCOPE_BASE_URL
base_url = settings.DASHSCOPE_BASE_URL
url_ok = bool(base_url and base_url.startswith("http"))
results.append(check_item(
    "DASHSCOPE_BASE_URL",
    url_ok,
    detail=base_url if url_ok else "未配置",
    suggestion="请在 .env 中填写 DASHSCOPE_BASE_URL" if not url_ok else ""
))

# 5-6. 模型连通性（按钮触发，不自动调用）
# 放在按钮区域处理

# 7. SQLite 连通性
sqlite_ok = False
sqlite_detail = ""
try:
    from repositories import sqlite_repository
    with sqlite_repository.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]
        sqlite_ok = True
        sqlite_detail = f"连接正常，messages 表含 {count} 条记录"
except Exception as e:
    sqlite_detail = f"连接异常: {e}"
results.append(check_item(
    "SQLite 数据库",
    sqlite_ok,
    detail=sqlite_detail,
    suggestion="请检查 data/ 目录是否可写，或运行 reset_demo_data.py 重建" if not sqlite_ok else ""
))

# 8. ChromaDB 目录
chroma_dir = settings.CHROMA_DIR
chroma_ok = os.path.isdir(chroma_dir)
results.append(check_item(
    "ChromaDB 目录",
    chroma_ok,
    detail=chroma_dir if chroma_ok else f"目录不存在: {chroma_dir}",
    suggestion="请确认 data/chroma_db 目录存在且可读写" if not chroma_ok else ""
))

# 9. demo_documents 目录
demo_dir = str(settings.BASE_DIR / "demo_documents")
demo_ok = os.path.isdir(demo_dir)
results.append(check_item(
    "demo_documents 目录",
    demo_ok,
    detail="存在" if demo_ok else "不存在",
    suggestion="demo_documents 目录缺失，演示文档不可用" if not demo_ok else ""
))

# 10. WEATHER_DEMO_MODE（天气工具始终为演示模式）
results.append(check_item(
    "天气工具模式",
    True,
    detail="演示模式（WEATHER_DEMO_MODE）",
    suggestion=""
))

# 11. 第三方库导入检查
libs = ["plotly", "pandas", "chromadb", "openai", "streamlit"]
lib_issues = []
for lib in libs:
    try:
        __import__(lib)
    except ImportError:
        lib_issues.append(lib)

results.append(check_item(
    "第三方库导入",
    len(lib_issues) == 0,
    detail="全部正常" if not lib_issues else f"缺失: {', '.join(lib_issues)}",
    suggestion=f"执行 pip install {' '.join(lib_issues)}" if lib_issues else ""
))

# 12. 数据目录检查
data_dirs = ["data/raw_documents", "data/chroma_db", "logs"]
missing_dirs = [d for d in data_dirs if not os.path.isdir(str(settings.BASE_DIR / d))]
results.append(check_item(
    "数据存储目录",
    len(missing_dirs) == 0,
    detail="全部存在" if not missing_dirs else f"缺失: {', '.join(missing_dirs)}",
    suggestion="缺失目录将在首次启动时自动创建，或手动创建" if missing_dirs else ""
))

# 渲染自检结果
st.markdown("### 📋 系统自检结果")
st.dataframe(results, use_container_width=True, hide_index=True)

# 统计
ok_count = sum(1 for r in results if "正常" in r["状态"])
warn_count = sum(1 for r in results if "警告" in r["状态"])
fail_count = sum(1 for r in results if "异常" in r["状态"])

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("✅ 正常", f"{ok_count} 项")
with c2:
    st.metric("⚠️ 警告", f"{warn_count} 项")
with c3:
    st.metric("❌ 异常", f"{fail_count} 项")

# 模型连通性测试（按钮触发）
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
            st.error("❌ 未配置 API Key，无法进行连通性测试。请在 .env 中填写 DASHSCOPE_API_KEY。")
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
