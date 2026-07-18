# MedAgent

面向医患双端的一体化智能医学 Agent 平台。融合 ReAct Agent 编排引擎、Adaptive-RAG 检索管道、三层记忆系统、MCP 工具框架和多模态交互能力。

## 快速开始

```bash
# 1. 启动所有服务（MySQL, Redis, ChromaDB, MinIO, Backend, Nginx）
cd docker && docker compose up -d

# 2. 安装后端依赖（需要 Python 3.11-3.12）
cd backend && pip install -r requirements.txt
pip install -e ".[test]" aiosqlite

# 3. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入 API Key

# 4. 启动后端（不使用 Docker 时）
cd backend && uvicorn app.main:app --reload --port 8000

# 5. 启动前端
cd frontend && npm install && npm run dev

# 6. 访问
# 前端: http://localhost:5173
# API 文档: http://localhost:8000/docs
# 生产模式（经 Nginx）: http://localhost
```

## 技术架构

```
Browser → Nginx(:80) → FastAPI(:8000)
                          ├─ /api/auth/*       → JWT 认证
                          ├─ /api/search       → RAG 检索
                          ├─ /api/chat/stream  → SSE 流式对话
                          ├─ /api/mcp/*        → MCP 工具调度
                          ├─ /api/voice/*      → Doubao 语音 STT/TTS
                          ├─ /api/report/*     → 多模态报告解读
                          ├─ /api/patient/*    → 患者档案/康复计划
                          └─ /api/doctor/*     → 医生患者查阅
```

核心技术栈：

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Python), Uvicorn |
| 数据库 | MySQL 8.0 (SQLAlchemy 2.0 async), Redis 7, ChromaDB |
| 文件存储 | MinIO |
| AI 模型 | Qwen-Max (阿里百炼), Qwen3:14b (Ollama 本地), Qwen3-Embedding-8B |
| 语音/视觉 | Doubao (火山引擎 ARK) — STT, TTS, OCR |
| 前端 | React 18, TypeScript, Vite, Zustand |
| 部署 | Docker Compose, Nginx |

## 目录结构

```
medagent/
├── docker/                    # Docker Compose + Nginx 配置
├── backend/                   # Python 后端
│   ├── app/
│   │   ├── api/               # REST API 路由
│   │   ├── core/              # 核心业务逻辑
│   │   │   ├── agent/         # Agent 编排 (ReAct + CoT)
│   │   │   ├── model_adapter/ # 模型适配器 (云/本地切换)
│   │   │   ├── rag/           # RAG 检索管道 (BM25 + 向量)
│   │   │   ├── memory/        # 记忆系统 (Redis + ChromaDB + MySQL)
│   │   │   ├── mcp/           # MCP 工具框架
│   │   │   └── multimodal/    # 多模态 (Doubao STT/TTS/OCR)
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── db/                # 数据库连接管理
│   │   └── middleware/        # 认证 + 身份路由中间件
│   └── tests/                 # 3 层测试 (unit / async_unit / api)
├── frontend/                  # React 前端
│   └── src/
│       ├── pages/             # 页面 (patient/, doctor/)
│       ├── components/        # 组件 (shared/, patient/, doctor/)
│       ├── stores/            # Zustand 状态管理
│       ├── api/               # API 调用封装
│       └── types/             # TypeScript 类型
└── README.md
```

## 环境变量

关键环境变量（详见 `backend/.env.example`）：

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 阿里百炼 API Key（必填） |
| `DOUBAO_API_KEY` | 火山引擎 Doubao API Key（语音/报告解读） |
| `DATABASE_URL` | MySQL 连接字符串 |
| `REDIS_URL` | Redis 连接字符串 |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB 地址 |
| `JWT_SECRET` | JWT 签名密钥 |
| `INFERENCE_BACKEND` | 推理后端 (auto/dashscope/ollama) |
| `EMBEDDING_BACKEND` | 向量化后端 |
| `RERANKER_BACKEND` | 重排序后端 |

## API 文档

启动后端后访问 Swagger UI: http://localhost:8000/docs

## 开发

```bash
# 运行所有后端测试
cd backend && pytest -v

# 按层级运行测试
cd backend && pytest tests/unit/ -v         # 纯单元测试
cd backend && pytest tests/async_unit/ -v   # 异步单元测试
cd backend && pytest tests/api/ -v          # API 集成测试

# 前端类型检查
cd frontend && npx tsc --noEmit

# Seed 测试数据
cd backend && python scripts/seed_data.py
```

**Python 版本**: 需要 3.11-3.12（Python 3.13 不兼容 numpy 1.x）
