# Backend 目录结构详解

## 根目录文件

### 配置文件

| 文件 | 作用 |
|------|------|
| `pyproject.toml` | **项目配置文件** - 定义项目名称、版本、依赖包（FastAPI、SQLAlchemy、LangChain 等）、构建设置 |
| `alembic.ini` | **数据库迁移配置** - Alembic 迁移工具的配置文件，指定迁移脚本位置、日志格式 |
| `.env.example` | **环境变量模板** - 示例环境配置文件，包含数据库 URL、JWT 密钥等配置项的示例值 |
| `.venv/` | **Python 虚拟环境** - 项目依赖的隔离环境（由 IDE 或手动创建） |

---

## app/ - 应用主目录

所有应用代码都在此目录下，按功能模块组织。

### app/__init__.py
**作用**：Python 包标识文件（通常为空，使 app 目录可作为模块导入）

### app/main.py
**作用**：**应用入口文件** - 创建和配置 FastAPI 应用实例

**核心功能**：
- 创建 FastAPI 应用
- 配置 CORS 中间件
- 注册全局异常处理器
- 注册所有 API 路由
- 定义应用生命周期（启动/关闭事件）
- 初始化 RAG 运行时

**关键代码**：
```python
def create_app() -> FastAPI:
    app = FastAPI(title="Owly Backend", ...)
    app.add_middleware(CORSMiddleware, ...)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app
```

---

## app/core/ - 核心基础设施层

提供全局通用的基础设施组件。

| 文件 | 作用 | 关键内容 |
|------|------|----------|
| `__init__.py` | 包标识 | - |
| `config.py` | **全局配置管理** | `Settings` 类（Pydantic BaseSettings），从 `.env` 读取所有配置项 |
| `database.py` | **数据库连接管理** | 异步引擎创建、会话工厂、自动建表函数 |
| `security.py` | **安全工具** | JWT 编解码、密码哈希（bcrypt）、token 生成 |
| `exceptions.py` | **全局异常处理** | 统一错误响应格式、异常处理器注册 |
| `logging.py` | **日志配置** | 结构化日志配置（structlog） |
| `pagination.py` | **分页工具** | 统一分页参数计算和响应格式 |

**配置项示例**（config.py）：
```python
class Settings(BaseSettings):
    database_url: str           # 数据库连接 URL
    jwt_secret: str             # JWT 签名密钥
    cors_origins: list[str]     # 允许的跨域来源
    redis_url: str              # Redis 连接 URL
    webhook_secret: str         # Webhook 签名密钥
    auto_create_schema: bool    # 是否自动创建表
```

---

## app/api/ - API 接口层

处理所有 HTTP 请求的入口。

### 核心文件

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `router.py` | **总路由注册** - 汇总所有子路由模块，统一注册到 `api_router` |
| `deps.py` | **依赖注入** - 提供数据库会话、认证上下文等依赖 |
| `compat.py` | **兼容工具** - 日期格式化等辅助函数 |

### router.py 详解
注册所有 API 子路由（25+ 个模块）：
```python
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(conversations.router, prefix="/conversations")
api_router.include_router(customers.router, prefix="/customers")
api_router.include_router(rag_router, prefix="/rag")
# ... 共 25+ 个子路由
```

### deps.py 详解
提供依赖注入函数：
- `get_session()` - 获取数据库会话（AsyncSession）
- `get_auth_context()` - 获取认证上下文（JWT 验证）
- `require_role(*roles)` - 角色权限检查

---

## app/api/v1/ - V1 版本 API 端点

包含所有具体的 API 端点实现，按业务模块划分。

| 文件 | 路径前缀 | 主要功能 |
|------|---------|---------|
| `__init__.py` | - | 包标识 |
| `auth.py` | `/auth` | 登录、注册、API Key 管理、密码修改 |
| `conversations.py` | `/conversations` | 对话 CRUD、消息、转接、合并、休眠、路由、宏执行 |
| `customers.py` | `/customers` | 客户 CRUD、标签、备注、黑名单 |
| `tickets.py` | `/tickets` | 工单 CRUD、分配、状态流转、优先级管理 |
| `knowledge.py` | `/knowledge` | 知识条目 CRUD、分类、搜索 |
| `ai_workspace.py` | `/knowledge/ai` | AI 开发信生成、投递、模板管理 |
| `automation.py` | `/automation` | 自动化规则 CRUD、条件匹配、动作执行 |
| `business_hours.py` | `/business-hours` | 营业时间配置、节假日管理 |
| `channels.py` | `/channels` | 渠道配置（Email/Phone/WhatsApp 等） |
| `webhooks.py` | `/webhooks` | Webhook CRUD、投递记录、重试管理 |
| `flows.py` | `/flows` | 流程编排 CRUD、节点配置、执行 |
| `campaigns.py` | `/campaigns` | 营销活动 CRUD、受众管理、效果统计 |
| `chat.py` | `/chat` | AI 聊天接口（调用 RAG 子系统） |
| `team.py` | `/team` | 团队成员 CRUD、部门管理、技能标签 |
| `sla.py` | `/sla` | SLA 规则 CRUD、违规检查 |
| `canned_responses.py` | `/canned-responses` | 快捷回复模板 CRUD |
| `activity.py` | `/activity` | 操作日志查询、审计 |
| `analytics.py` | `/analytics` | 数据统计、报表生成 |
| `stats.py` | `/stats` | 实时统计数据 |
| `export.py` | `/export` | 数据导出（CSV/Excel） |
| `realtime.py` | `/realtime` | SSE 事件流推送 |
| `tokens.py` | `/tokens` | Token 用量统计、成本分析 |
| `admin.py` | `/admin` | 管理后台接口 |
| `settings.py` | `/settings` | 系统设置管理 |
| `system.py` | `/system` | 系统信息查询 |
| `health.py` | `/health` | 健康检查 |

---

## app/domain/ - 领域层（业务逻辑）

实现核心业务逻辑，不依赖具体技术实现。

### 共享模块

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `shared/enums.py` | **共享枚举定义** - 角色、渠道类型、状态等枚举 |

**枚举示例**：
```python
class Role(StrEnum):
    VIEWER = "viewer"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class ConversationStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CLOSED = "closed"
```

### 各业务领域模块

每个模块包含相同的结构：
- `schemas.py` - 数据结构定义（Pydantic 模型）
- `service.py` - 业务逻辑实现
- 部分模块有 `engine.py` - 复杂业务引擎

| 模块 | 主要 Service | 主要功能 |
|------|-------------|---------|
| `auth/` | `AuthService` | 用户认证、API Key 验证、权限加载 |
| `conversation/` | `ConversationService`<br>`ConversationEngine` | 对话 CRUD、消息管理<br>路由策略、转接、合并、休眠、SLA 检查、宏执行 |
| `customer/` | `CustomerService` | 客户管理、标签、备注 |
| `knowledge/` | `KnowledgeService` | 知识条目管理 |
| `ai_workspace/` | `AIWorkspaceService` | AI 开发信生成、自动回复 |
| `automation/` | `AutomationService` | 自动化规则评估与执行 |
| `business_hours/` | `BusinessHoursService` | 营业时间检查 |
| `sla/` | `SLAService` | SLA 规则管理 |
| `webhooks/` | `WebhookService` | Webhook 管理 |
| `gdpr/` | `GDPRService` | 数据导出、删除、PII 脱敏 |
| `activity/` | `ActivityService` | 操作日志记录 |
| `admin/` | `AdminService` | 管理后台操作 |
| `settings/` | `SettingsService` | 系统设置管理 |
| `operations/` | `OperationsService` | 运维操作 |
| `tokens/` | `TokensService` | Token 用量管理 |
| `channels/` | `ChannelsService` | 渠道管理 |
| `flows/` | `FlowsService` | 流程管理 |
| `campaigns/` | `CampaignsService` | 营销活动管理 |
| `ticket/` | `TicketService` | 工单管理 |
| `canned_responses/` | `CannedResponsesService` | 快捷回复管理 |

---

## app/infrastructure/ - 基础设施层

提供技术实现细节（数据库访问、外部集成、实时通信等）。

### db/ - 数据库层

| 文件/目录 | 作用 |
|-----------|------|
| `__init__.py` | 包标识 |
| `base.py` | **SQLAlchemy 声明式基类** - 所有 ORM 模型的基类 `Base` |
| `unit_of_work.py` | **工作单元模式** - 事务管理（commit/rollback） |
| `models/` | **ORM 模型定义** - 表结构映射到 Python 类 |
| `repositories/` | **数据访问层** - 封装 CRUD 操作 |

#### models/ 目录
| 文件 | 包含的表 |
|------|---------|
| `auth.py` | `Admin`（管理员）, `ApiKey`（API 密钥） |
| `conversations.py` | `Conversation`, `Message`, `Tag`, `ConversationTag`, `InternalNote` |
| `team.py` | `TeamMember`, `Department`, `Ticket` |
| `knowledge.py` | `KnowledgeEntry` |
| `operations.py` | `Webhook`, `WebhookDelivery`, `SLARule`, `BusinessHours`, `CannedResponse`, `Flow`, `Channel`, `Campaign` |
| `rag.py` | RAG 子系统相关表 |

#### repositories/ 目录
每个 Repository 封装对一个或多个表的访问：
- `auth.py` - `AdminRepository`, `ApiKeyRepository`
- `conversations.py` - `ConversationRepository`, `MessageRepository`
- `customers.py` - `CustomerRepository`
- `knowledge.py` - `KnowledgeRepository`
- `automation.py` - `AutomationRuleRepository`
- `webhooks.py` - `WebhookRepository`, `WebhookDeliveryRepository`
- `tickets.py` - `TicketRepository`
- `analytics.py` - `AnalyticsRepository`
- `admin.py` - `AdminRepository`
- `settings.py` - `SettingsRepository`
- `operations.py` - `SLARuleRepository`, `BusinessHoursRepository`, `CannedResponseRepository`
- `flows.py` - `FlowRepository`
- `campaigns.py` - `CampaignRepository`

### integrations/ - 外部集成

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `ai.py` | **OpenAI Provider** - OpenAI API 调用封装（支持 Function Calling） |
| `channels.py` | **渠道适配器** - Email/Phone/WhatsApp 等渠道的收发适配器 |

### realtime/ - 实时通信

| 文件 | 作用 |
|------|------|
| `__init__.py` | **SSE 事件总线** - 实现 Server-Sent Events 实时推送 |

**事件类型**：
- `MESSAGE_NEW` - 新消息
- `CONVERSATION_UPDATED` - 对话更新
- `TICKET_NEW` - 新工单
- `TYPING_START/STOP` - 输入状态
- `AGENT_ONLINE/OFFLINE` - 客服状态

### webhooks/ - Webhook 投递

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `delivery.py` | **Webhook 投递服务** - 实现重试机制、HMAC 签名验证 |

**投递流程**：
1. 构建通知 Payload
2. 生成 HMAC-SHA256 签名
3. 发送 HTTP 请求
4. 记录投递结果
5. 失败自动重试（最多 3 次）

### events/ - 事件系统

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `types.py` | **领域事件定义** - `DomainEvent` 数据类 |
| `outbox.py` | **发件箱模式** - 可靠事件投递（内存实现） |

### tasks/ - 异步任务

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `ports.py` | **任务队列接口** - `TaskQueue` Protocol |
| `workflows.py` | **工作流调度器** - 事件触发的工作流 |

**工作流示例**：
- `conversation.created` → `sync_conversation_metrics`
- `message.received` → `evaluate_automation_rules`
- `webhook.delivery.failed` → `retry_webhook_delivery`

### query/ - 复杂查询

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标识 |
| `analytics.py` | **分析统计查询** - 封装复杂的统计分析 SQL |

---

## app/rag/ - RAG 子系统

独立的检索增强生成（RAG）模块，基于 LangChain/LangGraph。

### 目录结构

```
rag/
├── bootstrap.py              # RAG 运行时初始化
├── main.py                   # RAG 子应用入口
│
├── core/                     # RAG 核心配置
│   ├── config.py             # RAG 配置（模型、向量数据库等）
│   ├── checkpointer.py       # 对话检查点（LangGraph 持久化）
│   ├── prompts.py            # 提示词模板
│   ├── exceptions.py         # RAG 异常
│   └── logging.py            # RAG 日志
│
├── api/                      # RAG API 层
│   └── v1/                   # RAG V1 端点
│       ├── chat.py           # AI 聊天
│       ├── knowledge.py      # 知识库管理
│       ├── documents.py      # 文档管理
│       ├── chunks.py         # 分块管理
│       ├── categories.py     # 分类管理
│       ├── files.py          # 文件上传
│       ├── jobs.py           # 后台任务
│       ├── conversations.py  # RAG 对话
│       ├── knowledge_graph.py # 知识图谱
│       ├── system.py         # 系统信息
│       └── admin/            # RAG 管理端
│
├── db/                       # RAG 数据库层
│   ├── pg_client.py          # PostgreSQL 客户端
│   ├── base_repository.py    # 仓库基类
│   ├── repositories.py       # 仓库注册
│   ├── kb_repository.py      # 知识库仓库
│   ├── chunk_repository.py   # 分块仓库
│   ├── category_repository.py # 分类仓库
│   ├── file_repository.py    # 文件仓库
│   ├── job_repository.py     # 任务仓库
│   ├── conversation_repository.py # 对话仓库
│   └── init_db.py            # 数据库初始化
│
├── models/                   # RAG 数据模型
│   ├── requests.py           # 请求模型
│   └── responses.py          # 响应模型
│
└── services/                 # RAG 业务服务
    ├── chat_service.py       # 聊天服务（Supervisor Agent）
    ├── knowledge_service.py  # 知识库服务
    ├── document_service.py   # 文档服务
    ├── chunk_service.py      # 分块服务
    ├── chunk_splitter.py     # 分块策略
    ├── chunk_cleaner.py      # 分块清洗
    ├── embedding_service.py  # 向量嵌入
    ├── milvus_service.py     # Milvus 向量数据库
    ├── rerank_service.py     # 重排序
    ├── file_service.py       # 文件服务
    ├── job_service.py        # 任务服务
    ├── category_service.py   # 分类服务
    ├── conversation_service.py # 对话服务
    ├── oss_service.py        # 对象存储
    ├── doc_image_parser.py   # 文档图片解析
    ├── multimodal_embedding_service.py # 多模态嵌入
    ├── kg_whyhow_service.py  # 知识图谱（WhyHow）
    └── kg_graph_sync_service.py # 知识图谱同步
```

### 核心组件

#### chat_service.py
**作用**：聊天服务 - 调用 Supervisor Agent 处理用户消息

**工作流程**：
```
用户消息
    ↓
invoke_chat()
    ├─ 参数校验
    ├─ 获取 Supervisor Agent
    ├─ 调用 Agent.invoke()
    │   ├─ Agent 决策：直接回答 or 调用工具
    │   └─ 可能调用子代理（email_agent / search_agent）
    └─ 返回结构化结果
        ├─ response_content
        ├─ tools_used
        ├─ thoughts
        └─ usage
```

#### milvus_service.py
**作用**：Milvus 向量数据库操作封装
- 创建集合
- 插入向量
- 向量搜索
- 删除向量

#### embedding_service.py
**作用**：文本向量化
- 调用 OpenAI/DashScope 嵌入 API
- 批量向量化

---

## alembic/ - 数据库迁移

Alembic 数据库迁移工具的配置和脚本。

### 目录结构

```
alembic/
├── env.py                  # 迁移环境配置（加载模型、运行迁移）
├── script.py.mako          # 迁移文件模板
└── versions/               # 迁移版本文件
    ├── 0001_initial_schema.py  # 初始表结构
    └── ...                     # 后续迁移
```

### 关键文件

#### env.py
**作用**：配置 Alembic 运行环境
- 加载 SQLAlchemy 模型
- 配置数据库连接
- 执行迁移/回滚

#### versions/0001_initial_schema.py
**作用**：初始数据库表结构
- 创建所有表（Admin, Conversation, Message, Customer, etc.）
- 创建索引和外键约束

---

## 依赖关系总结

```
HTTP 请求
    ↓
app/main.py (FastAPI 应用)
    ↓
app/api/router.py (路由注册)
    ↓
app/api/v1/*.py (具体 API 端点)
    ├─ Depends(get_session) → AsyncSession
    ├─ Depends(get_auth_context) → AuthContext
    └─ 调用 Domain Service
        ↓
app/domain/*/service.py (业务逻辑)
    ├─ 调用 Repository
    └─ 调用 Unit of Work
        ↓
app/infrastructure/db/repositories/ (数据访问)
    └─ 使用 SQLAlchemy ORM
        ↓
app/infrastructure/db/models/ (表结构映射)
    └─ PostgreSQL 数据库

外部集成:
app/infrastructure/integrations/ai.py → OpenAI API
app/infrastructure/integrations/channels.py → Email/Phone/WhatsApp
app/infrastructure/webhooks/delivery.py → 外部 Webhook 接收方
app/infrastructure/realtime/__init__.py → SSE 客户端

RAG 子系统:
app/rag/services/chat_service.py → LangChain/LangGraph Agent
app/rag/services/milvus_service.py → Milvus 向量数据库
app/rag/services/embedding_service.py → 嵌入 API
```

---

## 技术栈总览

| 类别 | 技术 | 用途 |
|------|------|------|
| **Web 框架** | FastAPI | HTTP API 服务 |
| **ORM** | SQLAlchemy 2.0（异步） | 数据库访问 |
| **数据库** | PostgreSQL | 主数据存储 |
| **向量数据库** | Milvus | 向量搜索（RAG） |
| **AI 框架** | LangChain + LangGraph | RAG / Agent 编排 |
| **AI 模型** | OpenAI GPT-4o-mini | 对话生成 |
| **认证** | JWT + bcrypt | 用户认证 |
| **实时通信** | SSE | 事件推送 |
| **数据库迁移** | Alembic | 表结构版本管理 |
| **数据验证** | Pydantic v2 | 请求/响应验证 |
| **HTTP 客户端** | httpx | 外部 API 调用 |
| **缓存** | Redis | 会话缓存（配置） |
| **对象存储** | OSS（阿里云） | 文件存储（RAG） |
| **文档处理** | PyMuPDF, python-docx | PDF/Word 解析 |
| **日志** | structlog | 结构化日志 |
