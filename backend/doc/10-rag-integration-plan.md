# RAG 与 rag_agents 融入 Owly 后端方案

## 目标

将 `rag_backend_portable` 中的 RAG 能力从“独立便携服务”迁移为 Owly 后端的一等模块，复用现有 FastAPI 启动方式、配置体系、数据库迁移、认证上下文、服务分层和异步任务能力。

最终形态不是长期保留 `app/rag` 与 `app/rag_agents` 两个外来目录，而是逐步拆解并并入现有模块：

- API 层：`app/api/v1/knowledge.py`、`app/api/v1/ai_workspace.py` 或新增 `app/api/v1/rag.py`
- 领域层：`app/domain/knowledge`
- 基础设施层：`app/infrastructure`
- 后台任务层：`app/infrastructure/tasks`
- 数据模型与迁移：`app/infrastructure/db/models` 与 `alembic`

## 当前代码差异

现有 Owly 后端是模块化单体：

- `app/api/v1/*` 负责 HTTP 入口
- `app/domain/*` 放业务 schema 和 service
- `app/infrastructure/db/*` 放 SQLAlchemy 模型、repository、unit of work
- `app/infrastructure/integrations/*` 放外部 provider
- `app/core/config.py` 统一读取 `.env`
- `app/main.py` 统一生命周期、CORS、异常处理和路由挂载

`rag_backend_portable` 是独立服务：

- 自带 `app/main.py`
- 自带 `app/core/config.py`
- 自带 `app/db/*`，大量同步 psycopg2 SQL repository
- 自带 `agents/*` LangGraph 工作流
- 自带 Milvus、OSS、DashScope、LangGraph checkpointer 初始化
- API 前缀为 `/api/v1/...`

直接复制会造成这些问题：

- `app.*` 包名冲突，覆盖 Owly 原有 `app`
- RAG 配置导入时强制校验环境变量，导致主后端无法在无 RAG 配置时启动
- RAG 数据库建表绕开 Alembic
- RAG repository 绕开现有 SQLAlchemy session 与 unit of work
- RAG chat / knowledge 路由与现有 `/api/chat`、`/api/knowledge` 语义冲突
- RAG agent 和外部依赖缺失时会拖垮整个后端导入

## 推荐总体路线

采用两阶段策略：

1. 先完成兼容迁移，让 RAG 以可选模块方式挂载到 Owly 后端，接口可用且不影响原系统。
2. 再逐步内化，把 RAG 数据、服务、agent、外部适配器迁入 Owly 的现有分层。

这样可以先获得可运行能力，再降低长期维护成本。

## 阶段一：可选模块接入

### 目录建议

临时保留隔离命名空间：

```text
backend/app/rag/
backend/app/rag_agents/
```

隔离规则：

- 原便携版 `app.*` 导入改为 `app.rag.*`
- 原便携版 `agents.*` 导入改为 `app.rag_agents.*`
- RAG API 挂载到 `/api/rag/v1/...`
- 不占用原 `/api/knowledge` 和 `/api/chat`

### 路由接入

在 `app/api/router.py` 中挂载：

```python
from app.rag.api.v1 import router as rag_router

api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
```

为了保证主后端稳定，建议使用降级导入：

```python
try:
    from app.rag.api.v1 import router as rag_router
except ModuleNotFoundError as exc:
    rag_router = build_rag_unavailable_router(exc)
```

当 LangChain、LangGraph、Milvus、OSS 等依赖未安装时，主应用仍可启动，`/api/rag/...` 返回 503。

### 生命周期接入

新增：

```text
backend/app/rag/bootstrap.py
```

职责：

- 根据 `RAG_AUTO_INIT` 判断是否初始化 RAG runtime
- 初始化 RAG 表
- 初始化 LangGraph checkpointer
- 关闭时释放 checkpointer 连接池

在 `app/main.py` 的 lifespan 中调用：

```python
await init_rag_runtime()
...
await close_rag_runtime()
```

默认：

```env
RAG_AUTO_INIT=false
```

这样开发环境无 Milvus、OSS、DashScope 配置时也能启动原后端。

### 配置接入

阶段一可以保留 `app/rag/core/config.py`，但必须修改为“导入不校验，运行时校验”。

推荐新增方法：

```python
settings.validate_required_env()
```

只在以下场景调用：

- `RAG_AUTO_INIT=true`
- 上传文档
- 调用向量检索
- 调用模型生成
- 初始化 Milvus / OSS / LangGraph checkpointer

`.env.example` 需要补齐：

```env
RAG_AUTO_INIT=false
DASHSCOPE_API_KEY=""
LLM_MODEL="qwen-turbo"
MILVUS_HOST="localhost"
MILVUS_PORT="19530"
PG_HOST="localhost"
PG_PORT="5432"
PG_DB="owly"
PG_USER="postgres"
PG_PASSWORD="postgres"
OSS_ACCESS_KEY_ID=""
OSS_ACCESS_KEY_SECRET=""
OSS_BUCKET=""
```

### 依赖接入

将便携版 `requirements.txt` 合并进 `backend/pyproject.toml`。

建议先放入主依赖：

```toml
langgraph
langchain
langchain-core
langchain-openai
langgraph-checkpoint-postgres
openai
dashscope
psycopg-pool
pymilvus
oss2
alibabacloud_oss_v2
python-multipart
python-dotenv
tiktoken
pymupdf
python-docx
pandas
openpyxl
pageindex
```

后续可以改成 optional dependency：

```toml
[project.optional-dependencies]
rag = [...]
```

开发启动时使用：

```bash
pip install -e .[dev,rag]
```

## 阶段二：真正融入 Owly 分层

阶段二的目标是逐步删除临时 `app/rag` 外壳。

### 1. 数据模型迁移到 SQLAlchemy + Alembic

将 RAG 表迁入：

```text
app/infrastructure/db/models/knowledge.py
alembic/versions/*
```

建议新增或合并这些模型：

- `RagKnowledgeBase`
- `RagKnowledgeCategory`
- `RagKnowledgeFile`
- `RagKnowledgeJob`
- `RagKnowledgeChunk`
- `RagKnowledgeChunkOrigin`
- `RagKnowledgeChunkImage`
- `RagConversationSession`
- `RagConversationMessage`

当前便携版 SQL 中的表：

- `knowledge_base`
- `knowledge_category`
- `knowledge_category_file`
- `knowledge_file`
- `knowledge_job`
- `knowledge_chunk`
- `knowledge_chunk_origin`
- `knowledge_chunk_image`
- `conversation_session`
- `conversation_message`

可以先保留原表名，避免 Milvus metadata、已有数据和脚本失效。

### 2. Repository 迁移

将 `app/rag/db/*_repository.py` 重写为 SQLAlchemy repository：

```text
app/infrastructure/db/repositories/rag.py
```

使用：

- `AsyncSession`
- `SQLAlchemyUnitOfWork`
- `select`
- `insert/update/delete`

避免继续使用同步 `psycopg2` 与手写 SQL 作为主路径。

### 3. Service 迁移

将 RAG 业务服务拆进：

```text
app/domain/knowledge/rag_service.py
app/domain/knowledge/document_ingestion.py
app/domain/knowledge/chunking.py
app/domain/knowledge/rag_schemas.py
```

建议边界：

- `RagQueryService`：问答、流式问答
- `DocumentIngestionService`：上传、解析、切片、入库、建索引
- `RagConversationService`：RAG 会话记录
- `KnowledgeGraphSyncService`：知识图谱同步
- `ChunkService`：切片编辑、恢复、图片映射

### 4. 外部系统迁移到 infrastructure

将 RAG 外部依赖封装为 provider：

```text
app/infrastructure/integrations/rag_llm.py
app/infrastructure/integrations/vector_store.py
app/infrastructure/integrations/object_storage.py
app/infrastructure/integrations/rerank.py
app/infrastructure/integrations/document_parser.py
```

推荐端口：

```python
class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

class VectorStore(Protocol):
    async def search(self, query: str, *, collection: str, top_k: int) -> list[RetrievedChunk]: ...

class ObjectStorage(Protocol):
    async def upload(self, key: str, content: bytes, content_type: str) -> str: ...
```

实现：

- `DashScopeEmbeddingProvider`
- `MilvusVectorStore`
- `AlibabaOssStorage`
- `DashScopeRerankProvider`

### 5. LangGraph agent 迁移

将 `app/rag_agents` 拆为更明确的基础设施模块：

```text
app/infrastructure/agents/rag/
app/infrastructure/agents/supervisor/
```

LangGraph 节点可以保留，但节点内部不要直接 import repository 或全局 settings。建议通过 service / provider 注入上下文。

目标结构：

```text
app/infrastructure/agents/rag/graph.py
app/infrastructure/agents/rag/state.py
app/infrastructure/agents/rag/nodes/*.py
app/infrastructure/agents/rag/checkpointer.py
```

### 6. API 融合

建议保留现有 `/api/knowledge` 做客服知识库 CRUD。

新增 RAG 专属接口：

```text
GET    /api/knowledge/rag/health
GET    /api/knowledge/rag/models
POST   /api/knowledge/rag/query
POST   /api/knowledge/rag/query/stream
POST   /api/knowledge/rag/knowledge-bases
GET    /api/knowledge/rag/knowledge-bases
POST   /api/knowledge/rag/documents
GET    /api/knowledge/rag/documents
GET    /api/knowledge/rag/jobs/{job_id}
GET    /api/knowledge/rag/chunks
PUT    /api/knowledge/rag/chunks/{chunk_id}
```

阶段一的 `/api/rag/v1/...` 可以作为兼容路径，阶段二完成后逐步废弃。

### 7. 任务化文档处理

上传文档后不要在 HTTP 请求中同步完成解析、切片、embedding、Milvus 写入。

推荐流程：

1. API 创建 `knowledge_file`
2. API 创建 `knowledge_job`
3. API 返回 `job_id`
4. 后台任务执行：
   - 下载 OSS 文件
   - 解析文档
   - 清洗 chunk
   - 写 chunk 表
   - 生成 embedding
   - 写 Milvus
   - 更新 job 状态

后续可接入现有 Phase 2 的 Redis task queue。

## 权限与租户适配

所有 RAG API 应使用现有：

```python
Depends(get_auth_context)
```

并在 RAG 数据表中补充：

- `tenant_id` 或 `workspace_id`
- `created_by_id`
- `updated_by_id`

查询时必须按租户过滤：

```python
where(RagKnowledgeBase.tenant_id == auth.tenant_id)
```

如果当前项目还未完整启用多租户，先预留字段，默认写入 `"default"`。

## 错误处理

RAG 错误应映射到现有异常响应格式：

```json
{"error": "message"}
```

建议映射：

- 参数错误：400
- 知识库不存在：404
- job 冲突或重复文件：409
- 外部模型 / Milvus / OSS 错误：502
- RAG 未配置：503

不要让 DashScope、Milvus、OSS 的原始异常直接穿透到前端。

## 流式接口方案

保留 SSE：

```http
POST /api/knowledge/rag/query/stream
Content-Type: application/json
Accept: text/event-stream
```

事件：

```text
event: meta
data: {"requestId":"...","sources":[...]}

event: delta
data: {"text":"..."}

event: done
data: {"answer":"...","confidence":0.88}

event: error
data: {"error":"..."}
```

字段命名建议改为 Owly 前端常用 camelCase：

- `requestId`
- `sessionId`
- `imageMap`
- `finishReason`

内部 Python schema 仍可用 snake_case，通过 Pydantic alias 输出。

## 数据迁移顺序

1. 生成 Alembic migration，创建 RAG 表。
2. 保持表名与便携版一致。
3. 增加 Owly 需要的租户、用户、时间字段。
4. 用脚本校验旧表结构与新 ORM 模型一致。
5. 将 repository 从 `app/rag/db` 切到 `app/infrastructure/db/repositories/rag.py`。
6. 删除 runtime `init_db()` 建表逻辑。

## 测试计划

阶段一测试：

- 主后端无 RAG 依赖时可以启动。
- `/api/rag/v1/...` 在依赖缺失时返回 503。
- 安装 RAG 依赖后完整路由可导入。
- `RAG_AUTO_INIT=false` 时不连接 Milvus、OSS、DashScope。
- `RAG_AUTO_INIT=true` 且配置缺失时返回清晰错误。

阶段二测试：

- Alembic migration 可从空库迁移成功。
- 知识库 CRUD。
- 文档上传创建 job。
- job 状态流转。
- chunk 编辑与恢复。
- query 返回 answer、sources、confidence。
- SSE meta / delta / done / error 顺序正确。
- Milvus 不可用时返回 502，不影响主服务。

## 推荐实施任务拆分

### Task 1：稳定兼容层

- 保留 `app/rag`、`app/rag_agents`
- 路由挂 `/api/rag/v1`
- 依赖缺失时 503
- `RAG_AUTO_INIT=false` 默认关闭初始化
- 补 `.env.example`

### Task 2：RAG 表 Alembic 化

- 建 SQLAlchemy models
- 建 Alembic migration
- repository 仍可临时保持旧实现
- 确认表结构兼容

### Task 3：Repository 内化

- 用 AsyncSession 重写 `kb/file/job/chunk/conversation` repositories
- service 层改为依赖 repository interface
- 删除同步 pg_client 主路径

### Task 4：文档处理任务化

- 上传接口只创建 file/job
- 后台任务处理解析、切片、embedding、Milvus 写入
- job 查询接口返回进度

### Task 5：Agent 内化

- `rag_agents` 移到 `app/infrastructure/agents`
- 节点依赖 service/provider，不直接依赖全局 repository
- checkpointer 走统一 bootstrap

### Task 6：API 融合与兼容废弃

- 新增 `/api/knowledge/rag/*`
- `/api/rag/v1/*` 标记 deprecated
- 前端逐步切换
- 删除临时兼容层

## 验收标准

- 原有后端测试全部通过。
- 未配置 RAG 时，原 API 不受影响。
- 配置 RAG 后，OpenAPI 中能看到 RAG 接口。
- 能创建知识库、上传文档、查看 job、完成问答。
- RAG 表由 Alembic 管理，不再依赖启动时手写建表。
- Milvus、OSS、DashScope 失败时有明确错误响应和日志。
- `app/rag` 与 `app/rag_agents` 最终被拆分进 `domain` 和 `infrastructure`。

