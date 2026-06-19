# 模块 API 总览

说明：

- 当前后端通过 FastAPI 提供接口，默认公共前缀为 `/api`，配置项位于 `backend/app/core/config.py` 的 `api_v1_prefix`。
- 本文按 `backend/app/api/router.py` 实际挂载的路由整理；未挂载到主路由的旧兼容文件不列入可用接口。
- 接口大多需要登录认证，除系统初始化、登录、健康检查等特殊接口外，通常会通过 `get_auth_context` 校验当前用户。
- RAG 子系统统一挂载在 `/api/rag/v1` 下。
- `GET /api/docs` 可查看 Swagger 文档，`GET /api/openapi.json` 可获取 OpenAPI JSON。

## 一、核心业务 API

### 1. 健康检查 `health`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/health` | 返回服务健康状态，用于探活。 |

### 2. 认证 `auth`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/auth` | 查询当前认证状态、当前用户信息以及是否需要初始化系统。 |
| POST | `/api/auth/setup` | 初始化管理员账号，通常只在首次部署时使用。 |
| POST | `/api/auth/login` | 管理员登录，并写入认证 Cookie。 |
| POST | `/api/auth/logout` | 退出登录，并清理认证 Cookie。 |
| POST | `/api/auth` | 兼容入口，根据请求体中的动作统一处理 `setup`、`login`、`logout`。 |

### 3. 系统设置 `settings`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/settings` | 获取全局系统设置。 |
| PUT | `/api/settings` | 更新全局系统设置。 |

### 4. 会话 `conversations`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/conversations` | 分页查询会话列表，支持状态、渠道、搜索等筛选。 |
| POST | `/api/conversations` | 创建新会话。 |
| GET | `/api/conversations/{conversation_id}` | 获取单个会话详情。 |
| PUT | `/api/conversations/{conversation_id}` | 更新会话基本信息、状态、标签等。 |
| DELETE | `/api/conversations/{conversation_id}` | 删除会话。 |
| GET | `/api/conversations/{conversation_id}/messages` | 获取会话消息列表。 |
| POST | `/api/conversations/{conversation_id}/messages` | 向会话追加消息。 |
| POST | `/api/conversations/{conversation_id}/transfer` | 将会话转派给指定成员或部门。 |
| POST | `/api/conversations/{conversation_id}/merge` | 合并两个会话。 |
| POST | `/api/conversations/{conversation_id}/snooze` | 暂停/稍后处理会话。 |
| POST | `/api/conversations/{conversation_id}/satisfaction` | 提交会话满意度评分。 |
| POST | `/api/conversations/{conversation_id}/route-to` | 按策略路由会话。 |
| POST | `/api/conversations/{conversation_id}/macro` | 执行一组宏动作。 |
| GET | `/api/conversations/{conversation_id}/notes` | 获取会话内部备注。 |
| POST | `/api/conversations/{conversation_id}/notes` | 新增会话内部备注。 |

### 5. 客户 `customers`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/customers` | 分页查询客户列表，支持搜索、标签、封禁状态等筛选。 |
| POST | `/api/customers` | 创建客户。 |
| GET | `/api/customers/{customer_id}` | 获取客户详情。 |
| PUT | `/api/customers/{customer_id}` | 更新客户信息。 |
| DELETE | `/api/customers/{customer_id}` | 删除客户。 |
| GET | `/api/customers/{customer_id}/notes` | 获取客户备注。 |
| POST | `/api/customers/{customer_id}/notes` | 新增客户备注。 |
| GET | `/api/customers/{customer_id}/conversations` | 获取该客户关联的会话列表。 |
| GET | `/api/customers/{customer_id}/gdpr/export` | 导出该客户相关数据。 |
| DELETE | `/api/customers/{customer_id}/gdpr/delete` | 删除或匿名化该客户相关数据。 |

### 6. 工单 `tickets`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/tickets` | 分页查询工单列表，支持状态、优先级、部门、搜索等筛选。 |
| POST | `/api/tickets` | 创建工单。 |
| GET | `/api/tickets/{ticket_id}` | 获取工单详情。 |
| PUT | `/api/tickets/{ticket_id}` | 更新工单。 |
| DELETE | `/api/tickets/{ticket_id}` | 删除工单。 |

### 7. 知识库 `knowledge`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/knowledge/categories` | 获取业务知识分类列表。 |
| POST | `/api/knowledge/categories` | 创建业务知识分类。 |
| PUT | `/api/knowledge/categories/{category_id}` | 更新业务知识分类。 |
| DELETE | `/api/knowledge/categories/{category_id}` | 删除业务知识分类。 |
| GET | `/api/knowledge/entries` | 获取知识条目列表。 |
| POST | `/api/knowledge/entries` | 创建知识条目。 |
| PUT | `/api/knowledge/entries/{entry_id}` | 更新知识条目。 |
| DELETE | `/api/knowledge/entries/{entry_id}` | 删除知识条目。 |
| POST | `/api/knowledge/test` | 使用当前知识库内容测试 AI 回答效果。 |

### 8. AI 工作台 `knowledge-ai`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/knowledge/ai/outreach/generate` | 根据客户、知识条目、渠道和沟通目的生成外联内容草稿。 |
| POST | `/api/knowledge/ai/outreach/send` | 发送或记录外联草稿。 |
| POST | `/api/knowledge/ai/intent/analyze` | 分析客户沟通意图，并结合知识条目生成建议。 |
| GET | `/api/knowledge/ai/customer-service/settings` | 获取全局或单个客户的自动客服设置。 |
| PUT | `/api/knowledge/ai/customer-service/settings` | 新增或更新自动客服设置。 |
| GET | `/api/knowledge/ai/customer-service/logs` | 查询自动客服回复日志。 |
| GET | `/api/knowledge/ai/customer-service/customers` | 查询可配置自动客服的客户列表。 |

### 9. 自动化 `automation`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/automation` | 获取自动化规则列表，支持分页、类型、状态筛选。 |
| POST | `/api/automation` | 创建自动化规则。 |
| PUT | `/api/automation/{rule_id}` | 更新自动化规则。 |
| DELETE | `/api/automation/{rule_id}` | 删除自动化规则。 |

### 10. 营业时间 `business-hours`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/business-hours` | 获取营业时间配置。 |
| PUT | `/api/business-hours` | 更新营业时间配置。 |
| GET | `/api/business-hours/check` | 检查当前时间或指定时间是否处于营业时间内。 |

### 11. 渠道 `channels`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/channels` | 获取所有渠道配置与连接状态。 |
| POST | `/api/channels` | 保存一个渠道配置。 |
| GET | `/api/channels/whatsapp` | 获取 WhatsApp 渠道状态或二维码状态。 |
| POST | `/api/channels/whatsapp` | 执行 WhatsApp 渠道连接、断开或测试等动作。 |
| GET | `/api/channels/email` | 获取邮箱渠道状态。 |
| POST | `/api/channels/email` | 执行邮箱渠道连接、断开或测试等动作。 |
| GET | `/api/channels/{channel_type}` | 获取指定渠道配置。 |
| PUT | `/api/channels/{channel_type}` | 更新指定渠道配置。 |
| POST | `/api/channels/{channel_type}/action` | 执行指定渠道动作，如 `connect`、`disconnect`、`test`。 |
| POST | `/api/channels/{channel_type}` | 渠道动作兼容入口。 |
| POST | `/api/channels/phone/incoming` | 电话来电回调入口，返回语音交互响应。 |
| POST | `/api/channels/phone/gather` | 电话语音输入回调。 |
| POST | `/api/channels/phone/status` | 电话状态回调，并更新通话记录。 |

### 12. Webhook `webhooks`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/webhooks` | 获取 Webhook 列表。 |
| POST | `/api/webhooks` | 创建 Webhook。 |
| GET | `/api/webhooks/{webhook_id}` | 获取单个 Webhook 配置。 |
| PUT | `/api/webhooks/{webhook_id}` | 更新 Webhook。 |
| DELETE | `/api/webhooks/{webhook_id}` | 删除 Webhook。 |
| GET | `/api/webhooks/{webhook_id}/deliveries` | 获取 Webhook 投递记录。 |
| POST | `/api/webhooks/{webhook_id}/deliveries` | 兼容旧前端的投递重试入口，请求体传 `deliveryId`。 |
| POST | `/api/webhooks/{webhook_id}/deliveries/{delivery_id}/retry` | 重试指定投递记录。 |
| POST | `/api/webhooks/test` | 对指定 Webhook 发起测试请求。 |

### 13. Token `tokens`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/tokens/overview` | 获取 Token 余额、用量趋势和充值概览。 |
| POST | `/api/tokens/recharge/orders` | 创建 Token 充值订单。 |
| POST | `/api/tokens/recharge/orders/{order_id}/complete` | 将充值订单标记为完成，并更新余额。 |

### 14. 分析报表 `analytics`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/analytics` | 获取运营分析报表，支持 `period` 参数。 |
| GET | `/api/stats` | 获取统计概览。注意该路径也由 `stats` 模块定义，当前主路由中 `analytics` 先挂载。 |
| GET | `/api/activity` | 获取活动日志。注意该路径也由 `activity` 模块定义，当前主路由中 `analytics` 先挂载。 |

### 15. 管理后台 `admin`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/admin/users` | 获取管理员用户列表。 |
| POST | `/api/admin/users` | 创建管理员用户。 |
| PUT | `/api/admin/users/{user_id}` | 更新管理员用户。 |
| DELETE | `/api/admin/users/{user_id}` | 删除管理员用户。 |
| GET | `/api/admin/api-keys` | 获取 API Key 列表。 |
| POST | `/api/admin/api-keys` | 创建 API Key。 |
| PUT | `/api/admin/api-keys/{api_key_id}` | 更新 API Key。 |
| DELETE | `/api/admin/api-keys/{api_key_id}` | 删除 API Key。 |
| GET | `/api/admin/plugins` | 获取插件或扩展信息。 |

### 16. 营销活动 `campaigns`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/campaigns` | 获取营销活动列表。 |
| POST | `/api/campaigns` | 创建营销活动。 |
| GET | `/api/campaigns/{campaign_id}` | 获取营销活动详情。 |
| PUT | `/api/campaigns/{campaign_id}` | 更新营销活动。 |
| DELETE | `/api/campaigns/{campaign_id}` | 删除营销活动。 |
| POST | `/api/campaigns/{campaign_id}/execute` | 计算目标客户或执行营销活动。 |

### 17. 流程 `flows`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/flows` | 获取流程定义列表。 |
| POST | `/api/flows` | 创建流程定义。 |
| GET | `/api/flows/{flow_id}` | 获取流程详情。 |
| PUT | `/api/flows/{flow_id}` | 更新流程定义。 |
| DELETE | `/api/flows/{flow_id}` | 删除流程定义。 |
| POST | `/api/flows/{flow_id}/validate` | 校验流程节点结构是否合法。 |

### 18. AI 对话 `chat`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/chat` | 客服 AI 对话入口，可创建会话、写入消息、调用知识库和工具链并返回 AI 回复。 |

### 19. 团队 `team`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/team/departments` | 获取部门列表。 |
| POST | `/api/team/departments` | 创建部门。 |
| PUT | `/api/team/departments/{department_id}` | 更新部门。 |
| DELETE | `/api/team/departments/{department_id}` | 删除部门。 |
| GET | `/api/team/members` | 获取团队成员列表。 |
| POST | `/api/team/members` | 创建团队成员。 |
| PUT | `/api/team/members/{member_id}` | 更新团队成员。 |
| DELETE | `/api/team/members/{member_id}` | 删除团队成员。 |

### 20. 实时事件 `realtime`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/realtime` | 建立 SSE 实时订阅连接，支持全局频道和指定会话频道。 |
| POST | `/api/realtime/typing/{conversation_id}` | 发布指定会话的输入中状态。 |
| GET | `/api/realtime/stats` | 获取实时事件总线订阅数和频道数。 |

### 21. SLA `sla`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/sla` | 获取 SLA 规则列表，支持分页、渠道、优先级筛选。 |
| POST | `/api/sla` | 创建 SLA 规则。 |
| GET | `/api/sla/{rule_id}` | 获取 SLA 规则详情。 |
| PUT | `/api/sla/{rule_id}` | 更新 SLA 规则。 |
| DELETE | `/api/sla/{rule_id}` | 删除 SLA 规则。 |

### 22. 快捷回复 `canned-responses`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/canned-responses` | 获取快捷回复模板列表，支持分类、搜索、启用状态筛选。 |
| POST | `/api/canned-responses` | 创建快捷回复模板。 |
| GET | `/api/canned-responses/categories` | 获取快捷回复分类列表。 |
| GET | `/api/canned-responses/shortcut/{shortcut}` | 按快捷指令查找模板。 |
| GET | `/api/canned-responses/{response_id}` | 获取快捷回复详情。 |
| PUT | `/api/canned-responses/{response_id}` | 更新快捷回复模板。 |
| DELETE | `/api/canned-responses/{response_id}` | 删除快捷回复模板。 |
| POST | `/api/canned-responses/{response_id}/use` | 记录模板被使用一次，通常用于统计使用次数。 |

### 23. 活动日志 `activity`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/activity` | 分页查询操作日志，支持实体类型、起止时间筛选。注意该路径与 `analytics` 模块中的 `/api/activity` 重叠。 |

### 24. 统计概览 `stats`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/stats` | 获取会话、消息、工单、解决率、渠道分布等概览。注意该路径与 `analytics` 模块中的 `/api/stats` 重叠。 |

### 25. 数据导出 `export`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/export` | 按 `type` 和 `format` 导出数据，支持会话、客户、工单、知识库，格式支持 JSON/CSV。 |

## 二、RAG API

RAG 子系统挂载路径为 `/api/rag/v1`。如果 RAG 依赖缺失，主路由会返回 503，并提示缺失依赖。

### 1. RAG 系统信息

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/` | 返回 RAG 服务基本信息、默认模型和工作流说明。 |
| GET | `/api/rag/v1/models` | 获取可用模型列表。 |
| GET | `/api/rag/v1/health` | RAG 健康检查。 |

### 2. RAG 对话 `chat`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/rag/v1/chat/` | 与 Supervisor Agent 对话，支持会话级记忆。 |

### 3. RAG 知识问答 `knowledge`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/rag/v1/knowledge/` | 知识库问答，执行查询改写、分类、检索、过滤、重排、生成和质量检查流程。 |
| POST | `/api/rag/v1/knowledge/stream` | 知识库问答 SSE 流式输出。 |

### 4. RAG 文档处理 `documents`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| POST | `/api/rag/v1/documents/upload` | 上传文档到指定知识库，并提交后台切片任务。 |
| POST | `/api/rag/v1/documents/upload-to-category` | 上传单个文件到分类。 |
| POST | `/api/rag/v1/documents/batch-upload-to-category` | 批量上传文件到分类。 |
| GET | `/api/rag/v1/documents/excel-columns` | 读取分类文件中的 Excel 列信息。 |
| POST | `/api/rag/v1/documents/start-chunking-excel/{category_id}` | 对分类下的 Excel 文件启动切片任务。 |
| POST | `/api/rag/v1/documents/start-chunking/{category_id}` | 对分类下文件启动普通切片任务。 |
| POST | `/api/rag/v1/documents/search` | 在指定知识库或 collection 中搜索文档片段，支持混合检索、过滤、重排。 |
| GET | `/api/rag/v1/documents/image-proxy` | 通过 OSS key 代理返回图片内容。 |

### 5. RAG 任务 `jobs`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/jobs` | 查询指定知识库的切片/向量化任务列表。 |
| GET | `/api/rag/v1/jobs/{job_id}` | 获取任务详情。 |
| POST | `/api/rag/v1/jobs/{job_id}/upsert` | 将任务切片写入向量库。 |

### 6. RAG 分类 `categories`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/categories` | 获取 RAG 分类列表。 |
| POST | `/api/rag/v1/categories` | 创建 RAG 分类。 |
| GET | `/api/rag/v1/categories/{category_id}` | 获取分类及其文件列表。 |
| PUT | `/api/rag/v1/categories/{category_id}` | 更新分类。 |
| DELETE | `/api/rag/v1/categories/{category_id}` | 删除分类。 |
| DELETE | `/api/rag/v1/categories/{category_id}/files/{file_id}` | 删除分类下的单个文件。 |
| POST | `/api/rag/v1/categories/{category_id}/files/batch-delete` | 批量删除分类下的文件。 |

### 7. RAG 切片 `chunks`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/chunks/job/{job_id}` | 获取指定任务的切片列表。 |
| PUT | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}` | 编辑指定切片内容。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}/clean` | 清洗单个切片。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}/revert` | 回滚单个切片到原始内容。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/clean` | 批量清洗一个任务下的切片。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/revert` | 回滚一个任务下的全部切片。 |
| POST | `/api/rag/v1/chunks/clean-all` | 清洗全部切片。 |
| POST | `/api/rag/v1/chunks/revert-all` | 回滚全部切片。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/upsert` | 将指定任务切片写入向量库。 |
| POST | `/api/rag/v1/chunks/batch-upsert` | 批量将多个任务切片写入向量库。 |
| GET | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}/images` | 获取切片关联图片。 |
| POST | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}/images` | 给切片上传并关联图片。 |
| DELETE | `/api/rag/v1/chunks/job/{job_id}/chunk/{chunk_index}/images/{image_id}` | 删除切片关联图片。 |
| POST | `/api/rag/v1/chunks/resolve-images` | 将切片中的图片占位符解析为可访问图片信息。 |
| POST | `/api/rag/v1/chunks/resolve-oss-keys` | 将 OSS key 转成临时访问 URL。 |

### 8. RAG 文件 `files`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/files` | 查询指定知识库文件列表。 |
| DELETE | `/api/rag/v1/files` | 删除单个文件，请求体传 `file_id`。 |
| POST | `/api/rag/v1/files/batch-delete` | 批量删除文件。 |

### 9. RAG 会话 `conversations`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/conversations` | 查询指定知识库、用户的 RAG 会话列表。 |
| POST | `/api/rag/v1/conversations` | 创建 RAG 会话。 |
| GET | `/api/rag/v1/conversations/{session_id}/messages` | 获取 RAG 会话消息。 |
| DELETE | `/api/rag/v1/conversations/{session_id}` | 删除 RAG 会话。 |

### 10. RAG 管理：知识库集合 `admin/collections`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/admin/collections` | 获取知识库集合列表。 |
| POST | `/api/rag/v1/admin/collections` | 创建知识库集合，并初始化向量库 collection。 |
| GET | `/api/rag/v1/admin/collections/{kb_name}` | 获取指定知识库集合详情。 |
| PUT | `/api/rag/v1/admin/collections/{kb_name}` | 更新知识库集合配置。 |
| DELETE | `/api/rag/v1/admin/collections/{kb_name}` | 删除知识库集合，要求先删除其文件。 |

### 11. RAG 管理：配置 `admin/config`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/admin/config` | 查看 RAG 运行配置摘要，包括 Milvus、Postgres、Embedding 配置。 |

### 12. RAG 知识图谱 `knowledge-graph`

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/rag/v1/knowledge-graph/kb/{kb_name}` | 查询指定知识库已同步文件的知识图谱三元组统计和详情。 |

## 三、路径重叠与注意事项

- `/api/stats` 和 `/api/activity` 同时出现在 `analytics` 聚合模块与独立模块中；当前 `backend/app/api/router.py` 中 `analytics` 先挂载，建议后续统一保留一个入口，避免 OpenAPI 和运行时行为产生歧义。
- `backend/app/api/v1/operations.py` 与 `backend/app/api/v1/system.py` 中也定义了部分旧接口，但当前没有被 `api_router` 挂载，因此本文不作为可用接口列出。
- 电话、Webhook、RAG 上传、RAG SSE 等接口可能由外部平台或前端直接调用，请结合具体请求体 schema 查看对应 `schemas.py` 或接口函数参数。
