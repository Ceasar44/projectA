# 后端文档索引与维护规则

本文是后端文档入口。需要查接口、表结构、模块设计、异步任务/缓存说明时，优先从这里进入。

## 快速入口

| 需求 | 文档 | 说明 |
| --- | --- | --- |
| 查后端 API | [模块API总览.md](./模块API总览.md) | 按模块列出当前 FastAPI 实际挂载的接口、路径和作用。 |
| 查数据库表 | [后端数据库表结构与关系说明.md](./后端数据库表结构与关系说明.md) | 列出 SQLAlchemy 模型中的表、字段、约束和表关系。 |
| 查模块设计 | [modules/README.md](./modules/README.md) | 模块级业务流程、领域对象、对象关系、状态机和代码结构。 |
| 查队列/异步/缓存 | [后端队列异步任务缓存说明.md](./后端队列异步任务缓存说明.md) | 说明事件总线、BackgroundTasks、任务队列预留、缓存和 Redis 使用情况。 |

## 文档地图

### 1. API 文档

- [模块API总览.md](./模块API总览.md)

维护重点：

- 以 `backend/app/api/router.py` 的实际挂载为准。
- 新增、删除、改名 API 时必须同步更新。
- 如果 API 文件里有旧接口但没有被主路由挂载，不应放进“可用接口”清单，可放到注意事项里说明。

### 2. 数据库文档

- [后端数据库表结构与关系说明.md](./后端数据库表结构与关系说明.md)

维护重点：

- 以 `backend/app/infrastructure/db/models/*.py` 当前 SQLAlchemy 模型为准。
- 新增表、字段、外键、唯一约束、索引、状态字段时必须同步更新。
- Alembic 迁移和模型不一致时，要在文档里标出“模型现状”和“迁移现状”的差异。

### 3. 模块设计文档

- [modules/README.md](./modules/README.md)
- [modules/01-auth.md](./modules/01-auth.md)
- [modules/02-admin.md](./modules/02-admin.md)
- [modules/03-settings.md](./modules/03-settings.md)
- [modules/04-customers.md](./modules/04-customers.md)
- [modules/05-conversations.md](./modules/05-conversations.md)
- [modules/06-customer-support-agent.md](./modules/06-customer-support-agent.md)
- [modules/07-tickets-team.md](./modules/07-tickets-team.md)
- [modules/08-knowledge.md](./modules/08-knowledge.md)
- [modules/09-ai-workspace.md](./modules/09-ai-workspace.md)
- [modules/10-automation.md](./modules/10-automation.md)
- [modules/11-channels.md](./modules/11-channels.md)
- [modules/12-operations.md](./modules/12-operations.md)
- [modules/13-webhooks.md](./modules/13-webhooks.md)
- [modules/14-campaigns-flows.md](./modules/14-campaigns-flows.md)
- [modules/15-tokens.md](./modules/15-tokens.md)
- [modules/16-analytics-activity-export-realtime.md](./modules/16-analytics-activity-export-realtime.md)
- [modules/17-gdpr.md](./modules/17-gdpr.md)
- [modules/18-rag.md](./modules/18-rag.md)

维护重点：

- 每个模块文档保持同一结构：业务流程、领域对象与关系、状态机、模块结构。
- 新增模块时，在 `modules/` 下新增编号文件，并同步更新本索引和 [modules/README.md](./modules/README.md)。
- 合并模块或拆分模块时，先更新模块文档，再更新 API 总览和数据库文档。

### 4. 基础设施说明

- [后端队列异步任务缓存说明.md](./后端队列异步任务缓存说明.md)

维护重点：

- 如果引入 Redis、Celery、RQ、Arq、Kafka、RabbitMQ、定时任务、缓存层、分布式锁，要同步更新。
- 区分“实际接入主业务链路”和“仅有抽象/预留代码”。
- 涉及任务可靠性、重试、幂等、持久化时，要说明失败恢复策略。

## 维护规则

### 规则 1：代码是事实来源

文档应以代码为准，不以旧文档为准。优先级建议：

1. 实际运行路由：`backend/app/api/router.py`、`backend/app/main.py`
2. API 实现：`backend/app/api/v1/*.py`、`backend/app/rag/api/v1/*.py`
3. 领域逻辑：`backend/app/domain/**/service.py`
4. 数据模型：`backend/app/infrastructure/db/models/*.py`
5. 迁移文件：`backend/alembic/versions/*.py`
6. 旧文档或历史设计说明

### 规则 2：接口变化要同时更新三类文档

新增或修改 API 时，至少检查：

- [模块API总览.md](./模块API总览.md)
- 对应 [modules](./modules/README.md) 模块文档
- 如果涉及表结构，更新 [后端数据库表结构与关系说明.md](./后端数据库表结构与关系说明.md)

### 规则 3：表结构变化要写清楚影响范围

新增或修改数据表/字段时，文档中要说明：

- 字段类型、是否可空、默认值、索引、唯一约束。
- 外键关系和删除策略，例如 CASCADE、SET NULL。
- 字段属于业务状态、配置、审计、冗余快照还是扩展 JSON。
- 对 API、服务、前端展示是否有影响。

### 规则 4：状态值必须集中说明

如果模块出现新的状态字段，模块文档中应补充状态机，例如：

- `conversation.status`
- `ticket.status`
- `webhook_delivery.status`
- `knowledge_job.status`
- `campaign.status`
- `channel.status`

状态机至少说明：

- 初始状态。
- 允许的流转。
- 失败状态。
- 是否允许重试、回滚或重新打开。

### 规则 5：区分业务知识库和 RAG 知识库

文档中必须明确区分：

- 业务知识库：`category`、`knowledge_entry`，主要服务客服和 AI 工作台。
- RAG 知识库：`knowledge_base`、`knowledge_file`、`knowledge_job`、`knowledge_chunk`，主要服务文档检索和向量化。

不要只写“知识库”而不说明是哪一套。

### 规则 6：区分实际能力和预留设计

文档里遇到未完全接入的基础设施时，要明确标注：

- 已接入主链路
- 仅有接口/抽象
- 仅有配置项
- 未发现实际使用

例如当前：

- `RealtimeEventBus` 已接入主链路。
- `TaskQueue`、`InMemoryTaskQueue` 属于预留抽象。
- `REDIS_URL` 只是配置项，未发现实际 Redis 使用。

### 规则 7：敏感信息相关设计必须显式标注

涉及以下字段或功能时，文档应提示安全注意事项：

- API Key
- JWT Secret
- AI API Key
- SMTP/IMAP 密码
- Twilio Token
- Telegram Bot Token
- Webhook Secret
- 客户 PII 数据

建议说明是否脱敏、是否加密存储、是否限制角色访问。

### 规则 8：文档命名保持稳定

建议使用：

- 总览文档放在 `backend/doc/` 根目录。
- 模块设计文档放在 `backend/doc/modules/`。
- 模块文件使用两位数字前缀，例如 `01-auth.md`，便于排序。
- 文件名尽量表达内容，不要只写 `note.md`、`new.md`。

### 规则 9：不要把废弃文档混入主索引

如果保留历史文档，应单独放入 `backend/doc/archive/`，并在文档顶部注明：

```text
状态：历史文档，仅供参考，不代表当前实现。
```

主索引只链接当前可信文档。

### 规则 10：每次更新后做最小检查

建议检查：

```powershell
Get-ChildItem backend\doc -Recurse
git status --short backend\doc
```

如果更新的是 API 或数据库文档，可再用代码搜索确认：

```powershell
rg -n "include_router|@router\." backend\app\api backend\app\rag\api
rg -n "__tablename__|mapped_column|ForeignKey|relationship" backend\app\infrastructure\db\models
```

## 新增模块文档模板

```markdown
# 模块名称

## 业务流程

1. ...

## 领域对象与关系

- `ObjectA`：...
- `ObjectB`：...

关系说明：

- ...

## 状态机

```text
initial
  └─ action -> next
```

## 模块结构

- `backend/app/api/v1/...py`：...
- `backend/app/domain/.../service.py`：...
- `backend/app/domain/.../schemas.py`：...
- `backend/app/infrastructure/db/models/...py`：...
```

## 当前注意事项

- `backend/doc` 中以前的若干旧文档当前不在主索引内。如果需要保留历史，请移入 `backend/doc/archive/` 并标注历史状态。
- `/api/stats` 和 `/api/activity` 存在重复定义风险，详见 [模块API总览.md](./模块API总览.md)。
- 队列、缓存、异步任务目前多为进程内实现或预留抽象，生产化前应重新评估可靠性，详见 [后端队列异步任务缓存说明.md](./后端队列异步任务缓存说明.md)。
