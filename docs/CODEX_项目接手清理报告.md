# Codex 项目接手与冗余文件清理报告

生成日期：2026-07-08

## 1. 当前项目主入口确认

- 当前唯一推荐启动命令为：`streamlit run app.py`。
- `app.py` 是统一门户首页，内部通过 `st.session_state.app_mode` 在 `home`、`user`、`admin` 三种模式间切换。
- 用户端和管理端均在 `app.py` 内进入，不再需要单独启动 `user_app.py` 或 `admin_app.py`。
- 旧版 `user_app.py` 与 `admin_app.py` 已归档，不参与当前主流程。
- `.streamlit/config.toml` 已配置：
  ```toml
  [client]
  showSidebarNavigation = false
  ```

## 2. 当前项目结构梳理

- `app.py`：统一门户、用户端入口、管理端入口、管理员登录、导航分发。
- `page_views/`：当前实际页面渲染层，由 `app.py` 动态调用。
  - 用户端：`user_chat_view.py`、`user_history_view.py`、`user_agent_demo_view.py`
  - 管理端：`admin_knowledge_center_view.py`、`admin_dashboard_view.py`、`admin_session_logs_view.py`、`admin_tool_logs_view.py`、`admin_quality_view.py`、`admin_system_check_view.py`
- `services/`：业务服务层，包含 RAG、Agent、LLM、Embedding、批量导入、质量评估、工具注册等核心逻辑。本次未重构核心业务。
- `repositories/`：SQLite 与 ChromaDB 数据访问层。本次未修改表结构，未删除数据库或集合。
- `utils/`：通用工具层。本次仅修正 `auth_utils.py` 的旧 pages 链接残留，以及 `display_utils.py` 的旧错误字面量注释。
- `scripts/`：评估、演示、重置、文档转换脚本。本次未归档。
- `tests/`：单元测试。本次未删除。
- `docs/`：项目文档。本次更新 README、演示脚本、项目介绍书 Markdown，并新增本报告。
- `demo_documents/`：演示资料目录，按要求未删除、未移动。
- `data/`：运行数据目录，按要求未删除数据库、ChromaDB、raw_documents。

## 3. 冗余文件识别与处理结果

### 已归档文件

| 原路径 | 新路径 | 判断依据 |
| --- | --- | --- |
| `user_app.py` | `archive/legacy_entrypoints/user_app.py` | 当前 README 与 app.py 均确认统一入口为 `app.py`，全项目无主流程引用。 |
| `admin_app.py` | `archive/legacy_entrypoints/admin_app.py` | 当前管理端由 `app.py` 内部进入，全项目无主流程引用。 |
| `pages/1_校园咨询.py` | `archive/legacy_pages/1_校园咨询.py` | 旧 Streamlit 多页面文件，当前对应功能已迁移至 `page_views/user_chat_view.py`。 |
| `pages/2_知识库导入.py` | `archive/legacy_pages/2_知识库导入.py` | 旧单文件导入页，功能已合并至 `admin_knowledge_center_view.py`。 |
| `pages/3_对话历史.py` | `archive/legacy_pages/3_对话历史.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/user_history_view.py`。 |
| `pages/4_管理后台_知识库管理.py` | `archive/legacy_pages/4_管理后台_知识库管理.py` | 旧知识库管理页，功能已合并至统一知识库入口。 |
| `pages/5_管理后台_数据看板.py` | `archive/legacy_pages/5_管理后台_数据看板.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/admin_dashboard_view.py`。 |
| `pages/6_管理后台_会话日志.py` | `archive/legacy_pages/6_管理后台_会话日志.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/admin_session_logs_view.py`。 |
| `pages/7_挑战档_Agent演示.py` | `archive/legacy_pages/7_挑战档_Agent演示.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/user_agent_demo_view.py`。 |
| `pages/8_管理后台_工具调用日志.py` | `archive/legacy_pages/8_管理后台_工具调用日志.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/admin_tool_logs_view.py`。 |
| `pages/9_管理后台_回答质量评估.py` | `archive/legacy_pages/9_管理后台_回答质量评估.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/admin_quality_view.py`。 |
| `pages/10_系统自检.py` | `archive/legacy_pages/10_系统自检.py` | 旧多页面文件，当前对应功能已迁移至 `page_views/admin_system_check_view.py`。 |
| `pages/11_管理后台_批量导入.py` | `archive/legacy_pages/11_管理后台_批量导入.py` | 旧批量导入页，功能已合并至统一知识库入口。 |
| `page_views/admin_knowledge_import_view.py` | `archive/legacy_pages/page_views_compat/admin_knowledge_import_view.py` | 已迁移提示页，未被 `app.py`、脚本或测试引用。 |
| `page_views/admin_batch_import_view.py` | `archive/legacy_pages/page_views_compat/admin_batch_import_view.py` | 已迁移提示页，未被 `app.py`、脚本或测试引用。 |
| `page_views/admin_knowledge_manage_view.py` | `archive/legacy_pages/page_views_compat/admin_knowledge_manage_view.py` | 已迁移提示页，未被 `app.py`、脚本或测试引用。 |
| `logs/app.log` | `archive/antigravity_reports/app_legacy_JCD_paths.log` | 历史运行日志包含旧工作区盘符路径，不属于当前运行数据，归档后由应用后续重新生成新日志。 |

### 已删除缓存

- 删除了项目源码目录下的 `__pycache__/` 与 `*.pyc`。
- 明确未处理 `.venv/` 内部缓存，避免破坏现有虚拟环境内容。
- 未删除 `.env`、`demo_documents/`、`data/`、SQLite 数据库、ChromaDB 数据。

### 暂不处理的疑似冗余

- `pages/` 空目录：旧页面文件已归档，目录本身暂留为空目录，不影响 `showSidebarNavigation = false`。
- `docs/AIZS_项目介绍书.docx`：本次只更新 Markdown 源文档，未重生成 Word 文件，建议后续如需交付 Word 版再同步。
- `.venv/`：当前虚拟环境解释器失效，但目录包含依赖文件；本次不删除，建议后续重建。

## 4. 归档目录说明

- `archive/legacy_entrypoints/`：保存旧版独立启动入口。
- `archive/legacy_pages/`：保存旧 Streamlit 多页面文件，以及已迁移的兼容提示视图。
- `archive/antigravity_reports/`：保存历史工具或历史运行产物，本次归档了包含旧路径的历史日志。

## 5. 文档更新内容

- `README.md`
  - 删除当前结构中对根目录 `user_app.py`、`admin_app.py`、旧 `pages/` 当前页面层的描述。
  - 补充 `archive/` 归档目录说明。
  - 确认唯一启动命令为 `streamlit run app.py`。
- `docs/demo_script.md`
  - 将演示入口从旧的“批量导入”导航改为“知识库导入与管理”。
  - 将旧入口文件说明改为已归档。
  - 将登录与导航说明统一到 `app.py`。
- `docs/AIZS_项目介绍书.md`
  - 将物理结构中的前端展示层从旧 `pages/` 改为当前 `page_views/`。
  - 将导航与登录隔离说明从 `auth_utils` 修正为 `app.py` 主入口状态机。

## 6. 导航清理结果

- 首页：仅保留“进入用户端”和“进入管理端”两个主要入口。
- 用户端：保留“智能咨询”“对话历史”“Agent 智能演示”和“返回系统首页”。
- 管理端：登录后仅保留：
  - 知识库导入与管理
  - 数据看板
  - 会话日志
  - 工具调用日志
  - 回答质量评估
  - 系统自检
  - 退出登录
  - 返回系统首页
- 知识库入口已统一为 `📚 知识库导入与管理`。
- `page_views/admin_knowledge_center_view.py` 已包含：
  - 多文件导入，上传一个文件也可用
  - ZIP 导入
  - 演示文档一键导入
  - 已入库文档列表
  - 批量删除已选文档
  - 清除失败导入记录

## 7. 安全搜索结果

- 非归档目录中未发现旧工作区盘符路径或旧本地文件链接。
- 非归档目录中未发现旧样式安全开关字面量。
- 非归档目录中未发现空值直接参与百分比乘法的旧错误写法。
- 非归档目录中未发现推荐启动旧用户端或旧管理端入口的命令。
- 非归档目录中未发现对旧多页面文件的侧边栏导航调用。
- 允许存在的历史说明包括 README 中对 `archive/legacy_entrypoints/` 与 `archive/legacy_pages/` 的归档说明。

## 8. 测试命令和结果

当前机器没有可用的项目 Python 运行环境：

- `D:\AIZS\.venv\Scripts\python.exe` 指向不存在的 `C:\Users\16284\AppData\Local\Programs\Python\Python311\python.exe`。
- 系统 PATH 中没有可用 `python`。
- `py -3` 未找到已安装 Python。
- Codex 运行时 Python 为 3.12，可执行语法检查，但未安装项目依赖；直接挂载 `.venv/Lib/site-packages` 会因 NumPy/Pandas 的 Python 3.11 编译扩展与 Python 3.12 不兼容而失败。

已执行命令结果：

| 命令 | 结果 |
| --- | --- |
| `python -m unittest discover -s tests` | 使用 Codex Python 3.12 执行，失败。原因：缺少 `openai`、`python-dotenv` 等依赖。 |
| `python scripts/evaluate_intent_routing.py` | 失败。原因：缺少 `openai`。 |
| `python scripts/demo_challenge_scenarios.py` | 失败。原因：缺少 `python-dotenv`。 |
| `python -m py_compile app.py` | 通过。 |
| `python -m compileall -q page_views services repositories utils scripts config tests` | 通过。 |

## 9. 启动检查结果

启动命令 `streamlit run app.py` 未能完成，原因是当前环境没有可用 Streamlit：

- `where streamlit` 未找到命令。
- `.venv\Scripts\streamlit.exe --version` 失败，原因是 `.venv` 指向的 Python 3.11 已不存在。
- 使用 Codex Python 执行 `python -m streamlit run app.py` 失败，原因是未安装 `streamlit`。

因此，本次无法在浏览器中完成首页、用户端、管理端各页面的人工点击验收。代码层面已确认 `app.py` 的导航结构与目标一致。

## 10. 后续建议

1. 重建虚拟环境：
   ```powershell
   Remove-Item -Recurse -Force .venv
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. 重建环境后重新执行完整测试与启动验收。
3. 如需提交 Word 版项目介绍书，请根据已更新的 Markdown 重新生成 `docs/AIZS_项目介绍书.docx`。
4. 观察一段时间后，如确认不再需要历史入口和旧页面，可再人工决定是否删除 `archive/`。
5. 当前 `page_views/` 已较清晰，暂不建议重构 RAG、Agent、ChromaDB、SQLite、LLM 调用等核心业务。
