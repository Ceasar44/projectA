# Owly Backend 代码框架与流程分析

## 一、项目总览

Owly Backend 是一个基于 **FastAPI** 的 AI 客服系统后端，采用 **领域驱动设计（DDD）** + **分层架构**，使用 **SQLAlchemy（异步）** 作为 ORM，**PostgreSQL** 作为主数据库，**LangChain** 作为 RAG/AI 框架。

---

## 二、目录结构

```
backend/
├── alembic/                          # 数据库迁移工具
│   ├── env.py                        # 迁移环境配置
│   ├── script.py.mako                # 迁移文件模板
│   └── versions/                     # 迁移版本文件
│       └── 0001_initial_schema.py    # 初始表结构
│
├── app/
│   ├── main.py                       # 应用入口（创建 FastAPI 实例）
│   │
│   ├── core/                         # 核心基础设施层
│   │   ├── config.py                 # 全局配置（环境变量、数据库URL、JWT密钥等）
│   │   ├── database.py               # 数据库引擎、会话工厂
│   │   ├── security.py               # JWT 编解码、密码哈希
│   │   ├── exceptions.py             # 全局异常处理器
│   │   ├── logging.py                # 日志配置
│   │   └── pagination.py             # 分页工具
│   │
│   ├── api/                          # API 接口层（HTTP 入口）
│   │   ├── router.py                 # 总路由注册（汇总所有子路由）
│   │   ├── deps.py                   # 依赖注入（数据库会话、认证上下文）
│   │   ├── compat.py                 # 兼容工具（日期格式化等）
│   │   └── v1/                       # V1 版本 API 端点
│   │       ├── auth.py               # 认证（登录、注册、API Key）
│   │       ├── conversations.py      # 对话管理
│   │       ├── customers.py          # 客户管理
│   │       ├── tickets.py            # 工单管理
│   │       ├── knowledge.py          # 知识库
│   │       ├── ai_workspace.py       # AI 工作台（开发信生成等）
│   │       ├── automation.py         # 自动化规则
│   │       ├── business_hours.py     # 营业时间
│   │       ├── channels.py           # 渠道管理
│   │       ├── webhooks.py           # Webhook 管理
│   │       ├── flows.py              # 流程编排
│   │       ├── campaigns.py          # 营销活动
│   │       ├── chat.py               # AI 聊天接口
│   │       ├── team.py               # 团队管理
│   │       ├── sla.py                # SLA 规则
│   │       ├── canned_responses.py   # 快捷回复
│   │       ├── activity.py           # 活动日志
│   │       ├── analytics.py          # 数据分析
│   │       ├── stats.py              # 统计数据
│   │       ├── export.py             # 数据导出
│   │       ├── realtime.py           # SSE 实时推送
│   │       ├── tokens.py             # Token 用量
│   │       ├── admin.py              # 管理后台
│   │       ├── settings.py           # 系统设置
│   │       ├── system.py             # 系统信息
│   │       └── health.py             # 健康检查
│   │
│   ├── domain/                       # 领域层（业务逻辑）
│   │   ├── shared/                   # 共享枚举和工具
│   │   │   └── enums.py              # 角色枚举、渠道类型、状态枚举等
│   │   ├── auth/                     # 认证领域
│   │   │   ├── schemas.py            # 请求/响应数据结构
│   │   │   └── service.py            # 认证业务逻辑
│   │   ├── conversation/             # 对话领域
│   │   │   ├── schemas.py            # 对话数据结构
│   │   │   ├── service.py            # 对话业务逻辑
│   │   │   └── engine.py             # 对话引擎（路由、转接、合并、SLA检查）
│   │   ├── customer/                 # 客户领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── knowledge/                # 知识库领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── ai_workspace/             # AI 工作台领域
│   │   │   └── service.py
│   │   ├── automation/               # 自动化领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── business_hours/           # 营业时间领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── sla/                      # SLA 领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── channels/                 # 渠道领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── webhooks/                 # Webhook 领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── flows/                    # 流程编排领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── campaigns/                # 营销活动领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── ticket/                   # 工单领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── canned_responses/         # 快捷回复领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── activity/                 # 活动日志领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── admin/                    # 管理领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── settings/                 # 设置领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── operations/               # 运维操作领域
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── gdpr/                     # GDPR 合规模块
│   │   │   └── service.py
│   │   └── tokens/                   # Token 用量领域
│   │       └── service.py
│   │
│   ├── infrastructure/               # 基础设施层（技术实现）
│   │   ├── db/                       # 数据库层
│   │   │   ├── base.py               # SQLAlchemy 声明式基类
│   │   │   ├── unit_of_work.py       # 工作单元模式
│   │   │   ├── models/               # ORM 模型定义
│   │   │   │   ├── auth.py           # 用户、API Key 模型
│   │   │   │   ├── conversations.py  # 对话、消息、标签模型
│   │   │   │   ├── team.py           # 团队成员、部门、工单模型
│   │   │   │   ├── knowledge.py      # 知识库模型
│   │   │   │   ├── operations.py     # Webhook、SLA、营业时间等模型
│   │   │   │   └── rag.py            # RAG 相关模型
│   │   │   └── repositories/         # 数据访问层（Repository 模式）
│   │   │       ├── auth.py
│   │   │       ├── conversations.py
│   │   │       ├── customers.py
│   │   │       ├── knowledge.py
│   │   │       ├── automation.py
│   │   │       ├── channels.py
│   │   │       ├── webhooks.py
│   │   │       ├── tickets.py
│   │   │       ├── analytics.py
│   │   │       ├── admin.py
│   │   │       ├── settings.py
│   │   │       ├── operations.py
│   │   │       └── flows.py
│   │   │       └── campaigns.py
│   │   ├── integrations/             # 外部集成
│   │   │   ├── ai.py                 # OpenAI Provider（AI 调用封装）
│   │   │   └── channels.py           # 渠道适配器（Email/Phone/WhatsApp）
│   │   ├── realtime/                 # 实时通信
│   │   │   └── __init__.py           # SSE 事件总线
│   │   ├── webhooks/                 # Webhook 投递
│   │   │   └── delivery.py           # Webhook 投递服务（重试、签名）
│   │   ├── events/                   # 事件系统
│   │   │   ├── types.py              # 领域事件定义
│   │   │   └── outbox.py             # 发件箱模式
│   │   ├── tasks/                    # 异步任务
│   │   │   ├── ports.py              # 任务队列接口
│   │   │   └── workflows.py          # 工作流调度器
│   │   └── query/                    # 复杂查询
│   │       └── analytics.py          # 分析统计查询
│   │
│   └── rag/                          # RAG（检索增强生成）子系统
│       ├── bootstrap.py              # RAG 运行时初始化
│       ├── main.py                   # RAG 子应用入口
│       ├── core/                     # RAG 核心配置
│       │   ├── config.py             # RAG 配置
│       │   ├── checkpointer.py       # 对话检查点（持久化）
│       │   ├── prompts.py            # 提示词模板
│       │   ├── exceptions.py         # RAG 异常
│       │   └── logging.py            # RAG 日志
│       ├── api/                      # RAG API 层
│       │   └── v1/                   # RAG V1 端点
│       │       ├── chat.py           # RAG 聊天接口
│       │       ├── knowledge.py      # 知识库管理
│       │       ├── documents.py      # 文档管理
│       │       ├── chunks.py         # 文档分块
│       │       ├── categories.py     # 分类管理
│       │       ├── files.py          # 文件上传
│       │       ├── jobs.py           # 后台任务
│       │       ├── conversations.py  # RAG 对话
│       │       ├── knowledge_graph.py # 知识图谱
│       │       ├── system.py         # 系统信息
│       │       └── admin/            # RAG 管理端
│       │           ├── config.py
│       │           ├── collection.py
│       │           └── _deps.py
│       ├── db/                       # RAG 数据库层
│       │   ├── pg_client.py          # PostgreSQL 客户端
│       │   ├── base_repository.py    # 仓库基类
│       │   ├── repositories.py       # 仓库注册
│       │   ├── kb_repository.py      # 知识库仓库
│       │   ├── chunk_repository.py   # 分块仓库
│       │   ├── category_repository.py # 分类仓库
│       │   ├── file_repository.py    # 文件仓库
│       │   ├── job_repository.py     # 任务仓库
│       │   ├── conversation_repository.py # 对话仓库
│       │   ├── category_file_repository.py
│       │   ├── chunk_image_repository.py
│       │   └── init_db.py            # 数据库初始化
│       ├── models/                   # RAG 数据模型
│       │   ├── requests.py           # 请求模型
│       │   └── responses.py          # 响应模型
│       └── services/                 # RAG 业务服务
│           ├── chat_service.py       # 聊天服务（Supervisor Agent）
│           ├── knowledge_service.py  # 知识库服务
│           ├── document_service.py   # 文档服务
│           ├── chunk_service.py      # 分块服务
│           ├── chunk_splitter.py     # 分块策略
│           ├── chunk_cleaner.py      # 分块清洗
│           ├── embedding_service.py  # 向量嵌入
│           ├── milvus_service.py     # Milvus 向量数据库
│           ├── rerank_service.py     # 重排序
│           ├── file_service.py       # 文件服务
│           ├── job_service.py        # 任务服务
│           ├── category_service.py   # 分类服务
│           ├── conversation_service.py # 对话服务
│           ├── oss_service.py        # 对象存储
│           ├── doc_image_parser.py   # 文档图片解析
│           ├── multimodal_embedding_service.py # 多模态嵌入
│           ├── kg_whyhow_service.py  # 知识图谱（WhyHow）
│           └── kg_graph_sync_service.py # 知识图谱同步
│
├── alembic.ini                       # Alembic 配置
├── pyproject.toml                    # 项目依赖
└── doc/                              # 文档目录
```

---

## 三、架构分层

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HTTP 请求                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  API 层 (app/api/)                                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 职责: 接收 HTTP 请求，参数校验，调用 Service，返回响应       │   │
│  │ 组件: Router, Depends (依赖注入)                             │   │
│  │ 文件: api/v1/conversations.py, api/v1/auth.py, ...          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Domain 层 (app/domain/)                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 职责: 业务逻辑，不依赖具体技术实现                          │   │
│  │ 组件: Service (业务逻辑), Schema (数据结构), Engine (引擎)   │   │
│  │ 文件: domain/conversation/service.py, engine.py, ...         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Infrastructure 层 (app/infrastructure/)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 职责: 技术实现，数据库访问，外部服务调用                    │   │
│  │ 组件: Repository (数据访问), Model (ORM), Integration (集成) │   │
│  │ 文件: infrastructure/db/repositories/, models/, integrations/│   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Core 层 (app/core/)                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 职责: 全局配置、数据库连接、安全、异常处理                  │   │
│  │ 组件: Config, Database, Security, Exceptions                 │   │
│  │ 文件: core/config.py, database.py, security.py               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、核心模块详解

### 4.1 `core/` — 核心基础设施层

| 文件 | 作用 | 关键内容 |
|------|------|----------|
| `config.py` | 全局配置管理 | `Settings` 类（Pydantic BaseSettings），从 `.env` 读取配置 |
| `database.py` | 数据库连接管理 | 异步引擎创建、会话工厂、自动建表 |
| `security.py` | 安全工具 | JWT 编解码、密码哈希（bcrypt） |
| `exceptions.py` | 全局异常处理 | 统一错误响应格式 |
| `logging.py` | 日志配置 | 结构化日志 |
| `pagination.py` | 分页工具 | 统一分页参数和响应格式 |

**配置项：**

```python
class Settings(BaseSettings):
    database_url: str           # 数据库连接 URL
    jwt_secret: str             # JWT 签名密钥
    cors_origins: list[str]     # 允许的跨域来源
    redis_url: str              # Redis 连接 URL
    webhook_secret: str         # Webhook 签名密钥
    auto_create_schema: bool    # 是否自动创建表
    api_v1_prefix: str = "/api" # API 路径前缀
```

---

### 4.2 `api/` — API 接口层

#### 4.2.1 路由注册 (`api/router.py`)

所有 API 端点统一注册到 `api_router`，前缀为 `/api`：

```python
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(conversations.router, prefix="/conversations")
api_router.include_router(customers.router, prefix="/customers")
api_router.include_router(rag_router, prefix="/rag")
# ... 共 25+ 个子路由
```

#### 4.2.2 依赖注入 (`api/deps.py`)

| 依赖 | 作用 | 使用方式 |
|------|------|----------|
| `get_session()` | 获取数据库会话 | `session: AsyncSession = Depends(get_session)` |
| `get_auth_context()` | 获取认证上下文 | `auth: AuthContext = Depends(get_auth_context)` |
| `require_role(*roles)` | 角色权限检查 | `auth: AuthContext = Depends(require_role(Role.ADMIN))` |

**认证流程：**

```
请求到达
    │
    ├─ 检查 X-API-Key 头 → API Key 认证
    │
    └─ 检查 owly-token Cookie → JWT 认证
        │
        ├─ 解码 JWT → 获取 user_id
        ├─ 查询用户信息 → 构建 AuthContext
        └─ 返回认证上下文
```

#### 4.2.3 API 端点清单

| 模块 | 路径前缀 | 主要功能 |
|------|---------|---------|
| 认证 | `/auth` | 登录、注册、API Key 管理 |
| 对话 | `/conversations` | 对话 CRUD、消息、转接、合并、休眠、路由 |
| 客户 | `/customers` | 客户 CRUD、标签、备注 |
| 工单 | `/tickets` | 工单 CRUD、分配、状态流转 |
| 知识库 | `/knowledge` | 知识条目 CRUD |
| AI 工作台 | `/knowledge/ai` | AI 开发信生成、投递 |
| 自动化 | `/automation` | 自动化规则 CRUD、评估 |
| 营业时间 | `/business-hours` | 营业时间配置 |
| 渠道 | `/channels` | 渠道配置 |
| Webhook | `/webhooks` | Webhook CRUD、投递记录 |
| 流程 | `/flows` | 流程编排 CRUD |
| 营销 | `/campaigns` | 营销活动 CRUD |
| AI 聊天 | `/chat` | AI 对话接口 |
| 团队 | `/team` | 团队成员、部门管理 |
| SLA | `/sla` | SLA 规则 CRUD |
| 快捷回复 | `/canned-responses` | 快捷回复模板 CRUD |
| 活动日志 | `/activity` | 操作日志查询 |
| 分析 | `/analytics` | 数据统计 |
| 统计 | `/stats` | 统计数据 |
| 导出 | `/export` | 数据导出 |
| 实时 | `/realtime` | SSE 事件流 |
| Token | `/tokens` | Token 用量 |
| 管理 | `/admin` | 管理后台 |
| 设置 | `/settings` | 系统设置 |
| 系统 | `/system` | 系统信息 |
| 健康 | `/health` | 健康检查 |
| RAG | `/rag` | RAG 子系统（知识库、文档、分块、向量搜索） |

---

### 4.3 `domain/` — 领域层

领域层是业务逻辑的核心，每个子模块包含：

| 组件 | 作用 | 示例 |
|------|------|------|
| `schemas.py` | 数据结构定义（Pydantic 模型） | `ConversationCreate`, `MessageRead` |
| `service.py` | 业务逻辑实现 | `ConversationService.create_conversation()` |
| `engine.py` | 复杂业务引擎（仅 conversation 模块） | `ConversationEngine.route_conversation()` |

#### 4.3.1 核心领域服务

| 领域 | 服务 | 主要功能 |
|------|------|----------|
| `auth` | `AuthService` | 用户认证、API Key 验证、权限加载 |
| `conversation` | `ConversationService` | 对话 CRUD、消息管理 |
| `conversation` | `ConversationEngine` | 路由策略、转接、合并、休眠、SLA 检查、宏执行 |
| `customer` | `CustomerService` | 客户管理、标签、备注 |
| `knowledge` | `KnowledgeService` | 知识条目管理 |
| `ai_workspace` | `AIWorkspaceService` | AI 开发信生成、自动回复 |
| `automation` | `AutomationService` | 自动化规则评估与执行 |
| `business_hours` | `BusinessHoursService` | 营业时间检查 |
| `sla` | `SLAService` | SLA 规则管理 |
| `webhooks` | `WebhookService` | Webhook 管理 |
| `gdpr` | `GDPRService` | 数据导出、删除、PII 脱敏 |
| `activity` | `ActivityService` | 操作日志记录 |
| `admin` | `AdminService` | 管理后台操作 |
| `settings` | `SettingsService` | 系统设置管理 |

#### 4.3.2 ConversationEngine 详解

`ConversationEngine` 是最复杂的领域组件，负责对话的核心业务逻辑：

```
ConversationEngine
├── route_conversation()      # 对话路由分配
│   ├── ROUND_ROBIN          # 轮询策略
│   ├── LEAST_BUSY           # 最少工单策略
│   ├── SKILL_BASED          # 技能匹配策略
│   └── PRIORITY             # 优先级策略
├── transfer_conversation()   # 对话转接
├── merge_conversations()     # 对话合并
├── snooze_conversation()     # 对话休眠
├── check_sla_breaches()      # SLA 违规检查
└── execute_macro()           # 宏执行
    ├── set_status            # 设置状态
    ├── assign_department     # 分配部门
    ├── add_tag               # 添加标签
    ├── add_note              # 添加备注
    └── send_message          # 发送消息
```

---

### 4.4 `infrastructure/` — 基础设施层

#### 4.4.1 数据库层 (`infrastructure/db/`)

| 组件 | 作用 |
|------|------|
| `base.py` | SQLAlchemy 声明式基类 `Base` |
| `unit_of_work.py` | 工作单元模式（事务管理） |
| `models/` | ORM 模型定义（表结构映射） |
| `repositories/` | 数据访问层（CRUD 操作封装） |

**ORM 模型：**

| 模型文件 | 包含的表 |
|---------|---------|
| `auth.py` | `Admin`（管理员）, `ApiKey`（API 密钥） |
| `conversations.py` | `Conversation`（对话）, `Message`（消息）, `Tag`（标签）, `ConversationTag`（对话-标签关联）, `InternalNote`（内部备注） |
| `team.py` | `TeamMember`（团队成员）, `Department`（部门）, `Ticket`（工单） |
| `knowledge.py` | `KnowledgeEntry`（知识条目） |
| `operations.py` | `Webhook`（Webhook配置）, `WebhookDelivery`（投递记录）, `SLARule`（SLA规则）, `BusinessHours`（营业时间）, `CannedResponse`（快捷回复）, `Flow`（流程）, `Channel`（渠道）, `Campaign`（营销活动） |
| `rag.py` | RAG 子系统相关表 |

**Repository 模式：**

```python
# 每个 Repository 封装对数据库表的访问
class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload, customer_id) -> Conversation: ...
    async def get_detail(self, conversation_id) -> Conversation | None: ...
    async def list(self, page, limit, channel, status, search) -> tuple: ...
    async def update(self, conversation_id, payload) -> Conversation | None: ...
    async def exists(self, conversation_id) -> bool: ...
    async def touch(self, conversation_id) -> None: ...
```

**Unit of Work 模式：**

```python
class SQLAlchemyUnitOfWork:
    def __init__(self, session):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
```

#### 4.4.2 外部集成 (`infrastructure/integrations/`)

| 组件 | 作用 |
|------|------|
| `ai.py` | `OpenAIProvider` — OpenAI API 调用封装（支持 Function Calling） |
| `channels.py` | `ChannelAdapter` — 渠道适配器（Email/Phone/WhatsApp） |

**AI Provider 协议：**

```python
class AIProvider(Protocol):
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict: ...
```

**渠道适配器协议：**

```python
class ChannelAdapter(Protocol):
    async def receive(self, payload: dict) -> dict: ...
    async def send(self, payload: dict) -> dict: ...
```

#### 4.4.3 实时通信 (`infrastructure/realtime/`)

`RealtimeEventBus` 基于 SSE（Server-Sent Events）实现实时事件推送：

```
事件类型:
├── MESSAGE_NEW           # 新消息
├── MESSAGE_UPDATED       # 消息更新
├── CONVERSATION_NEW      # 新对话
├── CONVERSATION_UPDATED  # 对话更新
├── CONVERSATION_ASSIGNED # 对话分配
├── TICKET_NEW            # 新工单
├── TICKET_UPDATED        # 工单更新
├── TYPING_START          # 开始输入
├── TYPING_STOP           # 停止输入
├── AGENT_ONLINE          # 客服上线
├── AGENT_OFFLINE         # 客服下线
└── NOTIFICATION          # 通知

频道:
├── global                    # 全局频道
├── conversation:{id}         # 对话频道
└── user:{id}                 # 用户频道
```

#### 4.4.4 Webhook 投递 (`infrastructure/webhooks/`)

`WebhookDeliveryService` 负责将系统事件通知外部系统：

```
投递流程:
1. 构建通知 Payload
2. 生成 HMAC-SHA256 签名
3. 发送 HTTP 请求
4. 记录投递结果
5. 失败自动重试（最多 3 次，间隔 5s/30s/300s）
```

#### 4.4.5 事件系统 (`infrastructure/events/`)

```
DomainEvent: 领域事件定义
├── name: str        # 事件名称
├── payload: dict    # 事件数据
├── occurred_at: datetime  # 发生时间
└── event_id: str    # 事件唯一ID

OutboxRepository: 发件箱模式
└── InMemoryOutboxRepository: 内存实现（可替换为数据库实现）
```

#### 4.4.6 异步任务 (`infrastructure/tasks/`)

```
TaskQueue: 任务队列协议
└── InMemoryTaskQueue: 内存实现

WorkflowDispatcher: 工作流调度器
├── conversation.created → sync_conversation_metrics
├── message.received → evaluate_automation_rules
└── webhook.delivery.failed → retry_webhook_delivery
```

#### 4.4.7 复杂查询 (`infrastructure/query/`)

`AnalyticsQueryService` 封装复杂的统计分析查询：

```python
class AnalyticsQueryService:
    async def stats(self) -> dict[str, int]:
        # 返回 total_conversations, total_messages, total_tickets
```

---

### 4.5 `rag/` — RAG 子系统

RAG（Retrieval-Augmented Generation）子系统是一个相对独立的模块，负责知识库管理和 AI 对话。

#### 4.5.1 架构

```
rag/
├── core/           # 核心配置
│   ├── config.py   # RAG 配置（模型、向量数据库等）
│   ├── checkpointer.py  # 对话检查点（LangGraph 持久化）
│   ├── prompts.py  # 提示词模板
│   └── exceptions.py
│
├── api/v1/         # API 端点
│   ├── chat.py     # AI 聊天
│   ├── knowledge.py # 知识库管理
│   ├── documents.py # 文档管理
│   ├── chunks.py   # 分块管理
│   └── ...
│
├── db/             # 数据库层
│   ├── pg_client.py # PostgreSQL 客户端
│   ├── repositories.py # 仓库注册
│   └── *_repository.py # 各类仓库
│
├── models/         # 数据模型
│   ├── requests.py # 请求模型
│   └── responses.py # 响应模型
│
└── services/       # 业务服务
    ├── chat_service.py     # 聊天服务（Supervisor Agent）
    ├── knowledge_service.py # 知识库服务
    ├── embedding_service.py # 向量嵌入
    ├── milvus_service.py   # Milvus 向量数据库
    ├── rerank_service.py   # 重排序
    └── ...
```

#### 4.5.2 Chat Service 工作流程

```
用户消息
    │
    ▼
chat_service.invoke_chat()
    │
    ├─ 参数校验（模型、消息）
    │
    ├─ 获取 Supervisor Agent
    │   └─ get_supervisor_agent()
    │       ├─ email_agent     # 邮件子代理
    │       └─ search_agent    # 搜索子代理
    │
    ├─ 调用 Agent
    │   └─ agent.invoke({"messages": [HumanMessage(...)]}, config)
    │       │
    │       ├─ Agent 决策：直接回答 or 调用工具
    │       ├─ 如果需要：调用子代理（email_agent / search_agent）
    │       └─ 返回结果
    │
    └─ 返回结构化结果
        ├─ response_content  # AI 回复内容
        ├─ tools_used        # 使用的工具列表
        ├─ thoughts          # 决策过程
        └─ usage             # Token 用量
```

---

## 五、请求流程

### 5.1 完整请求生命周期

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. HTTP 请求到达                                                    │
│    POST /api/conversations/123/messages                             │
│    Body: {"role": "customer", "content": "我想退款"}                │
│    Cookie: owly-token=eyJhbGciOiJIUzI1NiIs...                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. FastAPI 中间件处理                                               │
│    ├─ CORSMiddleware: 添加跨域头                                    │
│    └─ Exception Handlers: 捕获异常                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 依赖注入                                                         │
│    ├─ get_session() → AsyncSession（数据库会话）                    │
│    └─ get_auth_context() → AuthContext（认证上下文）                │
│        ├─ 解码 JWT → user_id                                       │
│        └─ 查询用户 → AuthContext(role="agent", name="张三")        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. API 端点处理                                                     │
│    conversations.create_message()                                   │
│    ├─ 构建服务: build_service(session)                              │
│    │   └─ ConversationService(repo, repo, repo, uow)               │
│    ├─ 调用服务: service.create_message(conv_id, payload)            │
│    │   ├─ 验证对话存在                                              │
│    │   ├─ 创建消息记录                                              │
│    │   ├─ 更新对话时间                                              │
│    │   └─ 提交事务: uow.commit()                                   │
│    ├─ 发布实时事件: event_bus.emit_new_message()                    │
│    ├─ 评估自动化规则: automation_service.evaluate_rules()           │
│    │   └─ 匹配规则 → 执行宏（添加标签、发送消息等）                │
│    └─ 尝试 AI 自动回复: ai_workspace.maybe_auto_reply()            │
│        └─ 如果启用 AI → 调用 OpenAI → 发送回复 → 推送事件         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. 返回响应                                                         │
│    {                                                                │
│      "id": "msg_123",                                              │
│      "conversationId": "conv_456",                                 │
│      "role": "customer",                                           │
│      "content": "我想退款",                                        │
│      "createdAt": "2026-04-20T10:00:00Z"                           │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 服务构建模式

```python
# API 层构建服务实例
def build_service(session: AsyncSession) -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(session),
        message_repo=MessageRepository(session),
        customer_repo=CustomerRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )

# 依赖注入链
@router.post("/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    payload: MessageCreate,
    auth: AuthContext = Depends(get_auth_context),  # 认证
    session: AsyncSession = Depends(get_session),    # 数据库会话
):
    service = build_service(session)  # 构建服务
    item = await service.create_message(conversation_id, payload)  # 调用业务逻辑
    event_bus.emit_new_message(conversation_id, message_data)  # 发布事件
    return message_data  # 返回响应
```

---

## 六、模块间依赖关系

```
                    ┌─────────────┐
                    │   main.py   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  core/   │ │  api/    │ │  rag/    │
        │ config   │ │ router   │ │ bootstrap│
        │ database │ │ deps     │ └────┬─────┘
        │ security │ └────┬─────┘      │
        └────┬─────┘      │            │
             │            │            │
             │     ┌──────┼──────┐     │
             │     │      │      │     │
             │     ▼      ▼      ▼     │
             │  ┌─────┐┌─────┐┌─────┐ │
             │  │auth ││conv ││...  │ │
             │  │api  ││api  ││api  │ │
             │  └──┬──┘└──┬──┘└──┬──┘ │
             │     │      │      │    │
             │     ▼      ▼      ▼    │
             │  ┌──────────────────┐  │
             │  │    domain/       │  │
             │  │  service schemas │  │
             │  │  engine          │  │
             │  └────────┬─────────┘  │
             │           │            │
             │           ▼            │
             │  ┌──────────────────┐  │
             └─►│ infrastructure/  │  │
                │  db/repositories │  │
                │  db/models       │  │
                │  integrations    │  │
                │  realtime        │◄─┘
                │  webhooks        │
                │  events          │
                │  tasks           │
                │  query           │
                └──────────────────┘
```

**依赖规则：**

```
API 层 → 依赖 → Domain 层 → 依赖 → Infrastructure 层 → 依赖 → Core 层

API 层不能直接访问 Infrastructure 层（通过 Domain 层间接访问）
Domain 层不依赖 API 层
Infrastructure 层实现 Domain 层定义的接口
```

---

## 七、关键设计模式

### 7.1 Repository 模式

```python
# 数据访问封装在 Repository 中
class ConversationRepository:
    async def create(self, payload, customer_id) -> Conversation: ...
    async def get_detail(self, conversation_id) -> Conversation | None: ...
    async def list(self, page, limit, ...) -> tuple: ...

# Service 通过 Repository 访问数据
class ConversationService:
    def __init__(self, conversation_repo, message_repo, customer_repo, uow):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.customer_repo = customer_repo
        self.uow = uow
```

### 7.2 Unit of Work 模式

```python
# 事务管理
class SQLAlchemyUnitOfWork:
    async def commit(self) -> None:
        await self.session.commit()
    async def rollback(self) -> None:
        await self.session.rollback()

# Service 使用 UoW 管理事务
async def create_conversation(self, payload):
    conversation = await self.conversation_repo.create(payload, customer_id)
    await self.uow.commit()  # 提交事务
    return conversation
```

### 7.3 Protocol 模式（接口定义）

```python
# 使用 Python Protocol 定义接口
class AIProvider(Protocol):
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict: ...

class ChannelAdapter(Protocol):
    async def receive(self, payload: dict) -> dict: ...
    async def send(self, payload: dict) -> dict: ...

class TaskQueue(Protocol):
    async def enqueue(self, task_name: str, payload: dict) -> str: ...

class OutboxRepository(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
```

### 7.4 事件驱动模式

```python
# 发布事件
event_bus.emit_new_message(conversation_id, message_data)
event_bus.emit_conversation_update(conversation_id, changes)
event_bus.emit_typing(conversation_id, user_name, is_typing)

# 订阅事件（SSE 端点）
async def sse_endpoint(request):
    def callback(event: EventPayload):
        # 推送到客户端
        pass
    unsubscribe = event_bus.subscribe("global", callback)
```

---

## 八、应用启动流程

```
uvicorn app.main:app
    │
    ▼
create_app()
    │
    ├─ 创建 FastAPI 实例
    ├─ 添加 CORS 中间件
    ├─ 注册异常处理器
    └─ 注册路由（api_router）
    │
    ▼
lifespan() 启动
    │
    ├─ 加载配置: get_settings()
    ├─ 配置日志: configure_logging()
    ├─ 自动建表: create_schema()（如果启用）
    └─ 初始化 RAG: init_rag_runtime()
        └─ 初始化 Checkpointer（对话持久化）
    │
    ▼
应用就绪，等待请求
    │
    ▼
lifespan() 关闭
    │
    ├─ 关闭 RAG: close_rag_runtime()
    └─ 释放数据库引擎: dispose_engine()
```

---

## 九、数据库表关系

```
Admin ─────────────────────────────────────────────────────
    │
    └── 1:N ── ApiKey

Customer ──────────────────────────────────────────────────
    │
    └── 1:N ── Conversation
                  │
                  ├── 1:N ── Message
                  ├── 1:N ── InternalNote
                  ├── N:M ── Tag (通过 ConversationTag)
                  └── 1:N ── Ticket
                                │
                                ├── N:1 ── Department
                                └── N:1 ── TeamMember

TeamMember ────────────────────────────────────────────────
    │
    └── N:1 ── Department

KnowledgeEntry ────────────────────────────────────────────

Webhook ───────────────────────────────────────────────────
    │
    └── 1:N ── WebhookDelivery

SLARule ───────────────────────────────────────────────────

BusinessHours ─────────────────────────────────────────────

CannedResponse ────────────────────────────────────────────

Flow ──────────────────────────────────────────────────────

Channel ───────────────────────────────────────────────────

Campaign ──────────────────────────────────────────────────
```

---

## 十、技术栈总结

| 类别 | 技术 | 用途 |
|------|------|------|
| **Web 框架** | FastAPI | HTTP API 服务 |
| **ORM** | SQLAlchemy（异步） | 数据库访问 |
| **数据库** | PostgreSQL | 主数据存储 |
| **向量数据库** | Milvus | 向量搜索（RAG） |
| **AI 框架** | LangChain + LangGraph | RAG / Agent 编排 |
| **AI 模型** | OpenAI GPT-4o-mini | 对话生成 |
| **认证** | JWT + bcrypt | 用户认证 |
| **实时通信** | SSE | 事件推送 |
| **数据库迁移** | Alembic | 表结构版本管理 |
| **数据验证** | Pydantic | 请求/响应验证 |
| **HTTP 客户端** | httpx | 外部 API 调用 |
| **缓存** | Redis | 会话缓存（配置） |
| **对象存储** | OSS | 文件存储（RAG） |
