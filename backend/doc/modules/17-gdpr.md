# GDPR 模块

## 业务流程

1. 用户请求导出某个客户数据。
2. `GDPRService` 聚合客户、备注、会话、消息、工单等相关数据。
3. 用户请求删除客户数据时，可选择硬删除或匿名化策略。
4. 匿名化会保留业务记录，但清理姓名、邮箱、电话、消息中的敏感信息。
5. 数据保留策略可按时间清理过期数据。

## 领域对象与关系

- `GDPRService`：客户数据导出、删除、匿名化服务。
- `Customer`：GDPR 操作的核心对象。
- `CustomerNote`、`Conversation`、`Message`、`Ticket`：客户相关数据。
- `redact_pii`、`detect_pii`：PII 检测和脱敏工具函数。

关系说明：

- GDPR 模块不维护独立数据表。
- 通过 `customer.id` 找到客户主记录、备注、会话。
- 通过会话进一步找到消息和工单。

## 状态机

### 客户数据处理状态

```text
normal
  ├─ export -> normal
  ├─ anonymize -> anonymized
  └─ delete -> deleted
anonymized
  └─ 后续只保留脱敏后的业务记录
deleted
  └─ 不再可查询客户主数据
```

## 模块结构

- `backend/app/domain/gdpr/service.py`：GDPR 服务。
- `backend/app/api/v1/customers.py`：客户 GDPR API 入口。
- `backend/app/infrastructure/db/models/conversations.py`：客户、会话、消息、备注模型。
- `backend/app/infrastructure/db/models/team.py`：工单模型。
