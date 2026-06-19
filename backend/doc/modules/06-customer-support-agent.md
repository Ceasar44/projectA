# 客服 Agent 模块 Customer Support

## 业务流程

1. 客户消息进入会话后，系统可调用 `create_customer_message` 写入客户消息。
2. `CustomerSupportAgentService.reply_to_conversation` 加载会话、客户、业务设置和自动客服配置。
3. 服务根据客户消息识别意图、情绪、是否需要人工介入。
4. 如果允许自动回复，则构造模型上下文，调用 AI Provider。
5. AI 可使用工具查询客户历史、搜索知识库、创建/指派工单、添加内部备注、触发 Webhook 等。
6. 服务将 AI 回复写入消息表，并记录 `ai_auto_reply_log`。
7. 如果需要人工接管，则返回 handoff 回复并记录升级原因。

## 领域对象与关系

- `CustomerSupportAgentService`：客服 Agent 编排服务。
- `SupportToolRegistry`：工具注册和执行器。
- `SupportAgentConfig`：自动客服运行配置。
- `Conversation`、`Message`、`Customer`：Agent 的核心上下文。
- `KnowledgeEntry`：可被 Agent 引用的业务知识。
- `AiAutoReplyLog`：自动回复执行日志。
- `Ticket`：工具可创建或指派工单。

关系说明：

- `ai_auto_reply_log.conversation_id` 指向 `conversation.id`。
- `ai_auto_reply_log.customer_id` 指向 `customer.id`，客户删除后置空。
- 工具创建工单时会写入 `ticket`，可关联会话、部门、成员。
- 工具搜索知识时读取 `knowledge_entry`。

## 状态机

### Agent 回复决策

```text
收到客户消息
  ├─ 命中人工升级关键词/低信心/敏感意图 -> handoff
  ├─ 自动客服未启用 -> no_auto_reply
  └─ 自动客服启用 -> generating
generating
  ├─ 模型成功 -> sent
  ├─ 模型失败但可降级 -> fallback_sent
  └─ 工具/策略要求人工 -> escalated
```

### 日志状态

```text
sent
fallback_sent
escalated
failed
```

## 模块结构

- `backend/app/domain/customer_support/service.py`：Agent 编排、意图/情绪判断、自动回复。
- `backend/app/domain/customer_support/tools.py`：Agent 可调用工具。
- `backend/app/domain/customer_support/schemas.py`：Agent 配置和响应对象。
- `backend/app/api/v1/chat.py`：部分客服 AI 对话入口。
- `backend/app/domain/ai_workspace/service.py`：自动客服配置与日志查询。
