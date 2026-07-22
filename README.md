# 中南财经政法大学 (ZUEL) 智能校园咨询平台

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.1.0-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

本项目是专为**中南财经政法大学（Zhongnan University of Economics and Law, ZUEL）**打造的 AI 智能校园助手。该平台致力于为本校师生提供全方位的智能问答服务，包括教务咨询、生活指南、迎新导航、招生政策等。

系统基于前后端分离架构，前端采用现代化的 **Next.js + Tailwind CSS**（融合中南大标志性的“中南蓝”和“财大青”视觉元素），后端采用 **FastAPI**，底层通过大语言模型（LLM）、检索增强生成（RAG）、意图识别（Intent Routing）和智能体执行（Agent Execution）提供高精度回答。

## 🌟 核心特性

- **📚 专属知识库检索 (RAG)**：支持对海量校园文档（新生指南、奖学金办法、后勤服务等）的自动化分块、向量化（ChromaDB）与智能检索。
- **🤖 意图识别与动态路由**：基于 `dashscope` 提供的 LLM 能力与本地规则匹配，精准判断用户意图（如“天气”、“周边”、“教务”、“后勤”等），并将请求路由至特定智能体工具。
- **⚙️ 工具调用与智能体 (Agent)**：通过 `tool_registry` 挂载了天气查询（高德 API）、周边搜索、路线导航、知识库检索等工具，让模型能够主动执行复杂任务。
- **🎨 现代化交互界面**：基于 Next.js 打造的 ChatGPT 风格对话页面，以及由 AI 生成的专业级后台管理面板（ZUEL Admin Dashboard），用于直观管理文档和系统状态。
- **🛡️ 质量审计系统**：支持用户反馈（点赞/踩）与内置的自动化规则及 LLM 重复评估机制，确保持续提高问答质量。

## 🏗️ 架构概览

本项目在近期完成了全面的架构升级（Phase 1 & Phase 2/3），彻底抛弃了旧版的 Streamlit 渲染界面，重构为以下架构：

1. **Frontend (`/frontend`)**
   - **技术栈**：Next.js, React, Tailwind CSS, Lucide Icons
   - **特点**：全静态化支持、服务端代理 `/api` 至后端、适配深色/浅色模式，以及专门针对中南大视觉特征定制的 UI 设计。
2. **Backend (`api.py`)**
   - **技术栈**：FastAPI, Uvicorn, Python 3.11+
   - **特点**：对外暴露 RESTful API 供知识库管理，使用 Server-Sent Events (SSE) 流式返回聊天响应，确保流畅的用户体验。
3. **Core Services (`/services`, `/repositories`)**
   - **存储**：SQLite (元数据管理), ChromaDB (向量数据库)
   - **业务逻辑**：LLM 交互、文档处理与向量化、工具调度和意图解析模块。

## 🚀 快速启动

### 1. 环境准备

确保系统已安装 Python (>=3.11) 和 Node.js (>=18)。

1. 克隆代码并进入目录
2. 复制环境变量配置文件 `cp .env.example .env`
3. 编辑 `.env` 文件，填入你的 DASHSCOPE_API_KEY 和 AMAP_API_KEY 等配置

### 2. 启动后端 (FastAPI)

通过 pip 安装后端依赖：
> pip install -r requirements.txt

(可选) 初始化数据库与加载演示文档：
> python scripts/reset_demo_data.py

启动 FastAPI 服务 (运行在端口 8000)：
> uvicorn api:app --host 0.0.0.0 --port 8000 --reload

### 3. 启动前端 (Next.js)

进入 `frontend` 目录：
> cd frontend

安装依赖：
> npm install

启动开发服务器 (注意: 在 bash 脚本中需要带 `&` 放入后台):
> npm start

启动完成后，请在浏览器中访问：
- **聊天界面**: http://localhost:3000
- **后台管理**: http://localhost:3000/admin

## 📁 核心目录结构

- `api.py` : FastAPI 主入口程序
- `config/` : 配置文件 (加载 .env 等)
- `data/` : SQLite 数据库和 ChromaDB 向量库存储目录
- `demo_documents/` : 初始化用的测试/演示文档
- `frontend/` : Next.js 前端代码目录
- `mapping/` : 意图、位置和工具的基础映射规则
- `repositories/` : 数据访问层 (SQLite, ChromaDB 交互)
- `scripts/` : 运维与测试脚本 (重置数据、批量转化)
- `services/` : 核心业务逻辑 (Chat, RAG, Agent, Admin)
- `tests/` : 单元测试代码

## 📝 许可证

MIT License. 详见项目内的许可说明文件。
