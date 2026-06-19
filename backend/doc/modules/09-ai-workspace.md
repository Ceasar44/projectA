# AI 工作台模块 AI Workspace

## 业务流程

1. 用户选择客户、知识条目、渠道和沟通目的。
2. 调用外联生成接口，服务加载客户信息、知识条目和全局 AI 设置。
3. 服务调用 AI Provider 生成主题和正文，记录 token 用量，写入 `ai_outreach_draft`。
4. 用户确认后调用发送接口，系统创建 `ai_outreach_delivery`，必要时发送邮件。
5. 意图分析接口根据客户和沟通目标生成分析结果，写入 `ai_intent_analysis`。
6. 自动客服设置接口维护全局或客户级配置，写入 `ai_customer_service_config`。
7. 自动回复发生后，可查询 `ai_auto_reply_log`。

## 领域对象与关系

- `AiOutreachDraft`：AI 外联草稿。
- `AiOutreachDelivery`：外联投递记录。
- `AiIntentAnalysis`：客户意图分析结果。
- `AiCustomerServiceConfig`：自动客服配置。
- `AiAutoReplyLog`：自动客服执行日志。
- `Customer`：AI 工作台的目标客户。
- `KnowledgeEntry`：生成和分析时参考的业务知识。
- `Settings`：AI 模型、API Key、邮件配置来源。

关系说明：

- `ai_outreach_draft.customer_id` 指向 `customer.id`。
- `ai_outreach_delivery.draft_id` 指向 `ai_outreach_draft.id`，草稿删除后置空。
- `ai_outreach_delivery.customer_id` 指向 `customer.id`。
- `ai_intent_analysis.customer_id` 指向 `customer.id`。
- `ai_customer_service_config.customer_id` 指向 `customer.id`，全局配置时为空。
- `ai_auto_reply_log.conversation_id` 指向 `conversation.id`，`customer_id` 指向 `customer.id`。
- `knowledge_entry_ids` 是 JSON 数组，业务引用 `knowledge_entry.id`。

## 状态机

### 外联草稿

```text
draft
  ├─ send -> sent/queued
  ├─ auto_delivery_enabled=true -> queued
  └─ 用户修改 -> draft
queued
  ├─ 投递成功 -> sent
  └─ 投递失败 -> failed
```

### 自动客服配置

```text
disabled
  └─ enabled=true -> enabled
enabled
  └─ enabled=false -> disabled
```

## 模块结构

- `backend/app/api/v1/ai_workspace.py`：AI 工作台 API。
- `backend/app/domain/ai_workspace/service.py`：外联、意图分析、自动客服配置与日志。
- `backend/app/infrastructure/db/models/operations.py`：AI 工作台相关数据模型。
- `backend/app/infrastructure/integrations/ai.py`：AI Provider 封装。
- `backend/app/domain/tokens/service.py`：token 用量记录。
