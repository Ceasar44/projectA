# 模块 API 总览

说明:

- 本文档按模块整理当前项目的主要 API 接口。
- 路径以项目对外使用的 `/api/...` 形式展示。
- 功能描述尽量保持简短，便于快速查阅。
- 以原 TS API 设计为主，同时与当前 Python backend 的模块划分保持一致。

## 1. 认证 `auth`

- `GET /api/auth`
  - 查询当前登录状态，以及是否需要初始化系统。
- `POST /api/auth`
  - 统一处理 `setup / login / logout`。
- `POST /api/auth/setup`
  - 初始化系统管理员账号。
- `POST /api/auth/login`
  - 管理员登录。
- `POST /api/auth/logout`
  - 退出登录并清理认证 Cookie。

## 2. 系统设置 `settings`

- `GET /api/settings`
  - 获取系统全局设置。
- `PUT /api/settings`
  - 更新系统全局设置。

## 3. 会话 `conversations`

- `GET /api/conversations`
  - 按分页、状态、渠道、搜索条件获取会话列表。
- `POST /api/conversations`
  - 创建新会话。
- `GET /api/conversations/{id}`
  - 获取单个会话详情。
- `PUT /api/conversations/{id}`
  - 更新会话基本信息、状态、标签等。
- `DELETE /api/conversations/{id}`
  - 删除会话。

### 会话消息

- `GET /api/conversations/{id}/messages`
  - 获取会话消息列表。
- `POST /api/conversations/{id}/messages`
  - 向会话追加一条消息。

### 会话备注

- `GET /api/conversations/{id}/notes`
  - 获取会话内部备注列表。
- `POST /api/conversations/{id}/notes`
  - 创建会话内部备注。

### 会话扩展动作

- `POST /api/conversations/{id}/transfer`
  - 手动转派会话给指定成员。
- `POST /api/conversations/{id}/merge`
  - 合并两个会话。
- `POST /api/conversations/{id}/snooze`
  - 暂停/稍后处理会话。
- `POST /api/conversations/{id}/satisfaction`
  - 提交会话满意度评分。
- `POST /api/conversations/{id}/route-to`
  - 按策略自动路由到合适成员或部门。
- `POST /api/conversations/{id}/macro`
  - 执行一组宏动作。

## 4. AI 对话 `chat`

- `POST /api/chat`
  - AI 对话主入口，可创建会话、写入消息、调用知识库与工具链并返回 AI 回复。

## 5. 客户 `customers`

- `GET /api/customers`
  - 按分页、搜索、封禁状态获取客户列表。
- `POST /api/customers`
  - 创建客户。
- `GET /api/customers/{id}`
  - 获取客户详情。
- `PUT /api/customers/{id}`
  - 更新客户信息。
- `DELETE /api/customers/{id}`
  - 删除客户。

### 客户备注

- `GET /api/customers/{id}/notes`
  - 获取客户备注列表。
- `POST /api/customers/{id}/notes`
  - 新增客户备注。

### 客户会话

- `GET /api/customers/{id}/conversations`
  - 获取该客户关联的会话列表。

### GDPR

- `GET /api/customers/{id}/gdpr/export`
  - 导出该客户相关数据。
- `DELETE /api/customers/{id}/gdpr/delete`
  - 删除或匿名化该客户相关数据。

## 6. 工单 `tickets`

- `GET /api/tickets`
  - 按分页、状态、优先级、部门、搜索获取工单列表。
- `POST /api/tickets`
  - 创建工单。
- `GET /api/tickets/{id}`
  - 获取工单详情。
- `PUT /api/tickets/{id}`
  - 更新工单。
- `DELETE /api/tickets/{id}`
  - 删除工单。

## 7. 知识库 `knowledge`

### 分类

- `GET /api/knowledge/categories`
  - 获取知识分类列表。
- `POST /api/knowledge/categories`
  - 创建知识分类。
- `PUT /api/knowledge/categories/{id}`
  - 更新知识分类。
- `DELETE /api/knowledge/categories/{id}`
  - 删除知识分类。

### 条目

- `GET /api/knowledge/entries`
  - 获取知识条目列表。
- `POST /api/knowledge/entries`
  - 创建知识条目。
- `PUT /api/knowledge/entries/{id}`
  - 更新知识条目。
- `DELETE /api/knowledge/entries/{id}`
  - 删除知识条目。

### 测试

- `POST /api/knowledge/test`
  - 用当前知识库内容测试 AI 回答效果。

## 8. 团队 `team`

### 部门

- `GET /api/team/departments`
  - 获取部门列表。
- `POST /api/team/departments`
  - 创建部门。
- `PUT /api/team/departments/{id}`
  - 更新部门。
- `DELETE /api/team/departments/{id}`
  - 删除部门。

### 成员

- `GET /api/team/members`
  - 获取团队成员列表。
- `POST /api/team/members`
  - 创建团队成员。
- `PUT /api/team/members/{id}`
  - 更新团队成员。
- `DELETE /api/team/members/{id}`
  - 删除团队成员。

## 9. 自动化 `automation`

- `GET /api/automation`
  - 获取自动化规则列表。
- `POST /api/automation`
  - 创建自动化规则。
- `PUT /api/automation/{id}`
  - 更新自动化规则。
- `DELETE /api/automation/{id}`
  - 删除自动化规则。

## 10. 营业时间 `business-hours`

- `GET /api/business-hours`
  - 获取营业时间配置。
- `PUT /api/business-hours`
  - 更新营业时间配置。

## 11. SLA `sla`

- `GET /api/sla`
  - 获取 SLA 规则列表。
- `POST /api/sla`
  - 创建 SLA 规则。
- `PUT /api/sla/{id}`
  - 更新 SLA 规则。
- `DELETE /api/sla/{id}`
  - 删除 SLA 规则。

## 12. 快捷回复 `canned-responses`

- `GET /api/canned-responses`
  - 获取快捷回复模板列表。
- `POST /api/canned-responses`
  - 创建快捷回复模板。
- `PUT /api/canned-responses/{id}`
  - 更新快捷回复模板。
- `DELETE /api/canned-responses/{id}`
  - 删除快捷回复模板。

## 13. 渠道 `channels`

- `GET /api/channels`
  - 获取所有渠道配置与状态。
- `POST /api/channels`
  - 保存一个渠道配置。
- `GET /api/channels/{type}`
  - 获取指定渠道配置。
- `PUT /api/channels/{type}`
  - 更新指定渠道配置。
- `POST /api/channels/{type}`
  - 执行渠道动作兼容入口，如 `connect / disconnect / test`。
- `POST /api/channels/{type}/action`
  - 执行渠道动作标准入口，如 `connect / disconnect / test`。

### 特化渠道接口

- `GET /api/channels/email`
  - 获取 Email 渠道状态。
- `POST /api/channels/email`
  - 连接或断开 Email 渠道。
- `GET /api/channels/whatsapp`
  - 获取 WhatsApp 渠道状态或二维码状态。
- `POST /api/channels/whatsapp`
  - 连接或断开 WhatsApp 渠道。
- `POST /api/channels/sms`
  - 处理 SMS 渠道动作或兼容入口。
- `POST /api/channels/telegram`
  - 处理 Telegram 渠道动作或兼容入口。

### 电话回调

- `POST /api/channels/phone/incoming`
  - 处理电话来电入口，返回语音交互响应。
- `POST /api/channels/phone/gather`
  - 处理电话语音输入回调。
- `POST /api/channels/phone/status`
  - 处理电话状态回调并更新通话记录。

## 14. Webhook `webhooks`

- `GET /api/webhooks`
  - 获取 Webhook 列表。
- `POST /api/webhooks`
  - 创建 Webhook。
- `GET /api/webhooks/{id}`
  - 获取单个 Webhook 配置。
- `PUT /api/webhooks/{id}`
  - 更新 Webhook。
- `DELETE /api/webhooks/{id}`
  - 删除 Webhook。
- `GET /api/webhooks/{id}/deliveries`
  - 获取 Webhook 投递记录列表。
- `POST /api/webhooks/{id}/deliveries`
  - 兼容 TS 的投递重试入口，body 里传 `deliveryId`。
- `POST /api/webhooks/{id}/deliveries/{deliveryId}/retry`
  - 重试指定投递记录。
- `POST /api/webhooks/test`
  - 对指定 Webhook 发起测试请求。

## 15. Campaign `campaigns`

- `GET /api/campaigns`
  - 获取营销活动列表。
- `POST /api/campaigns`
  - 创建营销活动。
- `GET /api/campaigns/{id}`
  - 获取活动详情。
- `PUT /api/campaigns/{id}`
  - 更新活动。
- `DELETE /api/campaigns/{id}`
  - 删除活动。
- `POST /api/campaigns/{id}/execute`
  - 计算目标客户或执行活动。

## 16. Flow `flows`

- `GET /api/flows`
  - 获取流程定义列表。
- `POST /api/flows`
  - 创建流程定义。
- `GET /api/flows/{id}`
  - 获取流程详情。
- `PUT /api/flows/{id}`
  - 更新流程定义。
- `DELETE /api/flows/{id}`
  - 删除流程定义。
- `POST /api/flows/{id}/validate`
  - 校验流程节点结构是否合法。

## 17. 管理后台 `admin`

### 用户

- `GET /api/admin/users`
  - 获取管理员用户列表。
- `POST /api/admin/users`
  - 创建管理员用户。
- `PUT /api/admin/users/{id}`
  - 更新管理员用户。
- `DELETE /api/admin/users/{id}`
  - 删除管理员用户。

### API Keys

- `GET /api/admin/api-keys`
  - 获取 API Key 列表。
- `POST /api/admin/api-keys`
  - 创建 API Key。
- `PUT /api/admin/api-keys/{id}`
  - 更新 API Key。
- `DELETE /api/admin/api-keys/{id}`
  - 删除 API Key。

### 插件

- `GET /api/admin/plugins`
  - 获取插件或扩展信息。

## 18. 分析与统计 `analytics / stats / activity`

### Analytics

- `GET /api/analytics`
  - 获取分析报表数据。

### Stats

- `GET /api/stats`
  - 获取系统总览统计数据。

### Activity

- `GET /api/activity`
  - 获取操作日志列表。

## 19. 导出 `export`

- `GET /api/export`
  - 按类型导出数据，如会话、客户、工单、知识库。

## 20. 实时订阅 `realtime`

- `GET /api/realtime`
  - 建立 SSE 实时订阅连接。

## 21. 健康检查 `health`

- `GET /api/health`
  - 健康检查接口。

## 22. OpenAPI 文档

- `GET /api/openapi.json`
  - 获取 OpenAPI 规范 JSON。

