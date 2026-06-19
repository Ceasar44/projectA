# 模块设计文档索引

本目录按后端业务模块拆分文档。每个模块文档都包含：

- 业务流程
- 领域对象及对象关系
- 状态机描述
- 模块代码结构

## 模块列表

| 模块 | 文档 | 主要代码位置 |
| --- | --- | --- |
| 认证 | [01-auth.md](./01-auth.md) | `backend/app/domain/auth`、`backend/app/api/v1/auth.py` |
| 管理后台 | [02-admin.md](./02-admin.md) | `backend/app/domain/admin`、`backend/app/api/v1/admin.py` |
| 系统设置 | [03-settings.md](./03-settings.md) | `backend/app/domain/settings`、`backend/app/api/v1/settings.py` |
| 客户 | [04-customers.md](./04-customers.md) | `backend/app/domain/customer`、`backend/app/api/v1/customers.py` |
| 会话 | [05-conversations.md](./05-conversations.md) | `backend/app/domain/conversation`、`backend/app/api/v1/conversations.py` |
| 客服 Agent | [06-customer-support-agent.md](./06-customer-support-agent.md) | `backend/app/domain/customer_support` |
| 工单与团队 | [07-tickets-team.md](./07-tickets-team.md) | `backend/app/domain/ticket`、`backend/app/api/v1/team.py` |
| 业务知识库 | [08-knowledge.md](./08-knowledge.md) | `backend/app/domain/knowledge`、`backend/app/api/v1/knowledge.py` |
| AI 工作台 | [09-ai-workspace.md](./09-ai-workspace.md) | `backend/app/domain/ai_workspace`、`backend/app/api/v1/ai_workspace.py` |
| 自动化 | [10-automation.md](./10-automation.md) | `backend/app/domain/automation`、`backend/app/api/v1/automation.py` |
| 渠道 | [11-channels.md](./11-channels.md) | `backend/app/domain/channels`、`backend/app/api/v1/channels.py` |
| 运营配置 | [12-operations.md](./12-operations.md) | `business_hours`、`sla`、`canned_responses` |
| Webhook | [13-webhooks.md](./13-webhooks.md) | `backend/app/domain/webhooks`、`backend/app/api/v1/webhooks.py` |
| 营销活动与流程 | [14-campaigns-flows.md](./14-campaigns-flows.md) | `backend/app/domain/campaigns`、`backend/app/domain/flows` |
| Token | [15-tokens.md](./15-tokens.md) | `backend/app/domain/tokens`、`backend/app/api/v1/tokens.py` |
| 分析、活动、导出与实时 | [16-analytics-activity-export-realtime.md](./16-analytics-activity-export-realtime.md) | `analytics`、`activity`、`export`、`realtime` |
| GDPR | [17-gdpr.md](./17-gdpr.md) | `backend/app/domain/gdpr` |
| RAG | [18-rag.md](./18-rag.md) | `backend/app/rag`、`backend/app/rag_agents` |

## 维护要求

- 新增模块时，新建编号文档，并同步更新本文件和 [../INDEX.md](../INDEX.md)。
- 修改模块业务流程时，优先更新对应模块文档的“业务流程”和“状态机”。
- 修改领域对象或表关系时，同时检查 [../后端数据库表结构与关系说明.md](../后端数据库表结构与关系说明.md)。
- 修改 API 路径时，同时检查 [../模块API总览.md](../模块API总览.md)。
- 如果模块只是预留或未挂载到主路由，需要在文档里明确说明，不要写成已上线能力。
