# 会话模块 Conversations

## 业务流程

1. 渠道、前端或 AI 对话入口创建会话，写入 `conversation`。
2. 客户消息和客服/AI 回复写入 `message`。
3. 会话列表按状态、渠道、搜索条件分页展示。
4. 客服可更新会话状态、摘要、标签、满意度。
5. 会话可被转派、合并、暂挂、路由或执行宏动作。
6. 会话可生成工单，也可触发自动化规则和 AI 自动回复。

## 领域对象与关系

- `Conversation`：会话主对象。
- `Message`：会话消息。
- `InternalNote`：会话内部备注。
- `Tag`：会话标签。
- `ConversationTag`：会话-标签关联对象。
- `Ticket`：会话可关联多个工单。
- `ConversationService`：基础 CRUD 和消息写入。
- `ConversationRoutingEngine`：转派、合并、暂挂、路由、宏动作、SLA 检查。

关系说明：

- `conversation.id` 1 对多 `message.conversation_id`。
- `conversation.id` 1 对多 `internal_note.conversation_id`。
- `conversation` 多对多 `tag`，中间表为 `conversation_tag`。
- `conversation.id` 1 对多 `ticket.conversation_id`。
- `customer.id` 1 对多 `conversation.customer_id`。

## 状态机

会话状态主要由业务层字符串维护，常见状态如下：

```text
active
  ├─ resolve -> resolved
  ├─ close -> closed
  ├─ snooze -> snoozed
  └─ transfer/route -> active
snoozed
  ├─ 到期/恢复 -> active
  └─ close -> closed
resolved
  ├─ reopen -> active
  └─ close -> closed
closed
  └─ reopen -> active
```

合并流程：

```text
primary active/resolved
secondary active/resolved
  └─ merge -> secondary 消息/信息并入 primary，secondary 通常关闭或删除
```

## 模块结构

- `backend/app/api/v1/conversations.py`：会话 API。
- `backend/app/domain/conversation/service.py`：会话 CRUD 和消息逻辑。
- `backend/app/domain/conversation/engine.py`：路由、转派、合并、暂挂、宏动作。
- `backend/app/domain/conversation/schemas.py`：会话 schema。
- `backend/app/infrastructure/db/models/conversations.py`：会话、消息、备注、标签模型。
- `backend/app/infrastructure/db/repositories/conversations.py`：会话仓储。
