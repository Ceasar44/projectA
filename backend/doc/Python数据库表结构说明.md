# Python Backend 数据库表结构说明

来源:

- `backend/app/infrastructure/db/models/auth.py`
- `backend/app/infrastructure/db/models/conversations.py`
- `backend/app/infrastructure/db/models/knowledge.py`
- `backend/app/infrastructure/db/models/operations.py`
- `backend/app/infrastructure/db/models/team.py`

说明:

- 本文件描述的是 `backend` 目录下 Python SQLAlchemy 模型。
- 字段名保持 Python/数据库实际命名风格。
- 含义说明尽量简短。

## 1. `admin`

用途: 管理后台账号。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `username` | `String(100)` | 登录用户名 |
| `password` | `String(255)` | 哈希后的密码 |
| `name` | `String(200)` | 显示名称 |
| `role` | `String(20)` | 角色 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 2. `api_key`

用途: 外部 API 访问密钥。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | Key 名称 |
| `key` | `String(255)` | 实际密钥 |
| `is_active` | `Boolean` | 是否启用 |
| `last_used` | `DateTime?` | 上次使用时间 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 3. `customer`

用途: 客户主档案。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 客户姓名 |
| `email` | `String(300)` | 邮箱 |
| `phone` | `String(50)` | 电话 |
| `whatsapp` | `String(50)` | WhatsApp 联系方式 |
| `tags` | `String(500)` | 标签字符串 |
| `is_blocked` | `Boolean` | 是否封禁 |
| `metadata` | `JSON` | 扩展元数据 |
| `first_contact` | `DateTime` | 首次联系时间 |
| `last_contact` | `DateTime` | 最近联系时间 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 4. `customer_note`

用途: 客户备注。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `customer_id` | `String(36)` | 客户 ID |
| `content` | `Text` | 备注内容 |
| `author_name` | `String(200)` | 作者名称 |
| `created_at` | `DateTime` | 创建时间 |

## 5. `conversation`

用途: 客户会话主表。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `channel` | `String(50)` | 渠道类型 |
| `customer_name` | `String(200)` | 客户姓名 |
| `customer_contact` | `String(500)` | 客户联系方式 |
| `customer_id` | `String(36)?` | 关联客户 ID |
| `status` | `String(50)` | 会话状态 |
| `satisfaction` | `Integer?` | 满意度评分 |
| `summary` | `Text` | 会话摘要 |
| `metadata` | `JSON` | 会话扩展元数据 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 6. `message`

用途: 会话消息。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `conversation_id` | `String(36)` | 所属会话 ID |
| `role` | `String(50)` | 消息角色 |
| `content` | `Text` | 消息内容 |
| `media_type` | `String(100)?` | 媒体类型 |
| `media_url` | `String(2000)?` | 媒体地址 |
| `tool_calls` | `JSON?` | AI 工具调用信息 |
| `created_at` | `DateTime` | 创建时间 |

## 7. `internal_note`

用途: 会话内部备注。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `conversation_id` | `String(36)` | 会话 ID |
| `content` | `Text` | 备注内容 |
| `author_name` | `String(200)` | 作者名称 |
| `created_at` | `DateTime` | 创建时间 |

## 8. `tag`

用途: 会话标签定义。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(100)` | 标签名称 |
| `color` | `String(20)` | 标签颜色 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 9. `conversation_tag`

用途: 会话与标签的关联表。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `conversation_id` | `String(36)` | 会话 ID |
| `tag_id` | `String(36)` | 标签 ID |
| `created_at` | `DateTime` | 创建时间 |

## 10. `category`

用途: 知识库分类。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 分类名称 |
| `description` | `String(1000)` | 分类描述 |
| `icon` | `String(50)` | 分类图标 |
| `color` | `String(20)` | 分类颜色 |
| `sort_order` | `Integer` | 排序值 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 11. `knowledge_entry`

用途: 知识库条目。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `category_id` | `String(36)` | 所属分类 ID |
| `title` | `String(500)` | 条目标题 |
| `content` | `Text` | 条目正文 |
| `priority` | `Integer` | 优先级 |
| `is_active` | `Boolean` | 是否启用 |
| `version` | `Integer` | 版本号 |
| `metadata` | `JSON` | 扩展元数据 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 12. `settings`

用途: 系统全局配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(50)` | 主键，默认 `default` |
| `business_name` | `String(500)` | 企业名称 |
| `business_desc` | `String(5000)` | 企业描述 |
| `welcome_message` | `String(2000)` | 默认欢迎语 |
| `tone` | `String(50)` | AI 回复语气 |
| `language` | `String(20)` | 回复语言设置 |
| `ai_provider` | `String(50)` | AI 服务提供商 |
| `ai_model` | `String(100)` | AI 模型名称 |
| `ai_api_key` | `String(500)` | AI API 密钥 |
| `max_tokens` | `Integer` | AI 最大输出 token 数 |
| `temperature` | `Float` | AI 采样温度 |
| `smtp_host` | `String(500)` | SMTP 主机 |
| `smtp_port` | `Integer` | SMTP 端口 |
| `smtp_user` | `String(300)` | SMTP 用户名 |
| `smtp_pass` | `String(500)` | SMTP 密码 |
| `smtp_from` | `String(300)` | 发件人地址 |
| `imap_host` | `String(500)` | IMAP 主机 |
| `imap_port` | `Integer` | IMAP 端口 |
| `imap_user` | `String(300)` | IMAP 用户名 |
| `imap_pass` | `String(500)` | IMAP 密码 |
| `twilio_sid` | `String(200)` | Twilio SID |
| `twilio_token` | `String(200)` | Twilio Token |
| `twilio_phone` | `String(50)` | Twilio 电话号码 |
| `eleven_labs_key` | `String(200)` | ElevenLabs API Key |
| `eleven_labs_voice` | `String(200)` | ElevenLabs 音色配置 |
| `whatsapp_mode` | `String(50)` | WhatsApp 接入模式 |
| `whatsapp_api_key` | `String(500)` | WhatsApp API Key |
| `whatsapp_phone` | `String(50)` | WhatsApp 号码 |
| `telegram_bot_token` | `String(500)` | Telegram Bot Token |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 13. `channel`

用途: 渠道接入配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `type` | `String(50)` | 渠道类型 |
| `is_active` | `Boolean` | 是否启用 |
| `config` | `JSON` | 渠道配置 |
| `status` | `String(50)` | 渠道状态 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 14. `call_log`

用途: 电话呼叫记录。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `call_sid` | `String(100)` | 电话呼叫唯一标识 |
| `from` | `String(100)` | 来电号码 |
| `to` | `String(100)` | 目标号码 |
| `duration` | `Integer` | 通话时长 |
| `status` | `String(50)` | 通话状态 |
| `recording` | `String(2000)?` | 录音地址 |
| `summary` | `Text` | 通话摘要 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 15. `automation_rule`

用途: 自动化规则。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 规则名称 |
| `description` | `String(1000)` | 规则描述 |
| `type` | `String(100)` | 规则类型 |
| `is_active` | `Boolean` | 是否启用 |
| `conditions` | `JSON` | 触发条件 |
| `actions` | `JSON` | 执行动作 |
| `priority` | `Integer` | 优先级 |
| `trigger_count` | `Integer` | 触发次数 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 16. `business_hours`

用途: 营业时间配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(50)` | 主键，默认 `default` |
| `enabled` | `Boolean` | 是否启用营业时间 |
| `timezone` | `String(100)` | 时区 |
| `monday` | `String(50)` | 周一营业时间 |
| `tuesday` | `String(50)` | 周二营业时间 |
| `wednesday` | `String(50)` | 周三营业时间 |
| `thursday` | `String(50)` | 周四营业时间 |
| `friday` | `String(50)` | 周五营业时间 |
| `saturday` | `String(50)` | 周六营业时间 |
| `sunday` | `String(50)` | 周日营业时间 |
| `offline_message` | `String(500)` | 非营业时间提示语 |

## 17. `sla_rule`

用途: SLA 规则。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 规则名称 |
| `description` | `String(1000)` | 规则描述 |
| `channel` | `String(50)` | 适用渠道 |
| `priority` | `String(50)` | 适用优先级 |
| `first_response_mins` | `Integer` | 首次响应时限 |
| `resolution_mins` | `Integer` | 解决时限 |
| `is_active` | `Boolean` | 是否启用 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 18. `canned_response`

用途: 快捷回复模板。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `title` | `String(200)` | 模板标题 |
| `content` | `Text` | 模板内容 |
| `category` | `String(100)` | 模板分类 |
| `shortcut` | `String(50)` | 快捷命令 |
| `is_active` | `Boolean` | 是否启用 |
| `usage_count` | `Integer` | 使用次数 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 19. `webhook`

用途: 外部 Webhook 配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | Webhook 名称 |
| `description` | `String(1000)` | Webhook 描述 |
| `url` | `String(2000)` | 目标地址 |
| `method` | `String(10)` | 请求方法 |
| `headers` | `JSON` | 自定义请求头 |
| `is_active` | `Boolean` | 是否启用 |
| `trigger_on` | `String(200)` | 触发事件 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 20. `webhook_delivery`

用途: Webhook 投递记录。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `webhook_id` | `String(36)` | Webhook ID |
| `event` | `String(200)` | 事件名称 |
| `payload` | `JSON` | 投递载荷 |
| `status` | `String(50)` | 投递状态 |
| `status_code` | `Integer?` | HTTP 状态码 |
| `attempts` | `Integer` | 重试次数 |
| `last_error` | `Text?` | 最近错误信息 |
| `next_retry_at` | `DateTime?` | 下次重试时间 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 21. `activity_log`

用途: 操作审计日志。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `action` | `String(200)` | 动作名称 |
| `entity` | `String(100)` | 实体类型 |
| `entity_id` | `String(36)?` | 实体 ID |
| `description` | `Text` | 描述信息 |
| `user_id` | `String(36)?` | 操作人 ID |
| `user_name` | `String(200)` | 操作人名称 |
| `metadata` | `JSON` | 扩展元数据 |
| `request_id` | `String(100)?` | 请求 ID |
| `ip_address` | `String(100)?` | IP 地址 |
| `user_agent` | `String(1000)?` | User-Agent |
| `created_at` | `DateTime` | 创建时间 |

## 22. `campaign`

用途: 主动营销/触达活动。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 活动名称 |
| `description` | `String(1000)` | 活动描述 |
| `channel` | `String(50)` | 发送渠道 |
| `message` | `Text` | 消息正文 |
| `subject` | `String(500)` | 邮件主题 |
| `segments` | `JSON` | 客群筛选条件 |
| `status` | `String(50)` | 活动状态 |
| `scheduled_at` | `DateTime?` | 计划执行时间 |
| `sent_count` | `Integer` | 已发送数量 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 23. `flow`

用途: 对话流程编排定义。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 流程名称 |
| `description` | `String(1000)` | 流程描述 |
| `start_node_id` | `String(100)` | 起始节点 ID |
| `nodes` | `JSON` | 节点定义集合 |
| `is_active` | `Boolean` | 是否启用 |
| `trigger_count` | `Integer` | 触发次数 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 24. `department`

用途: 团队部门。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 部门名称 |
| `description` | `String(1000)` | 部门描述 |
| `email` | `String(300)` | 部门邮箱 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 25. `team_member`

用途: 团队成员/坐席。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `name` | `String(200)` | 成员姓名 |
| `email` | `String(300)` | 成员邮箱 |
| `phone` | `String(50)` | 成员电话 |
| `role` | `String(100)` | 成员角色 |
| `expertise` | `String(500)` | 专长领域 |
| `department_id` | `String(36)` | 所属部门 ID |
| `is_available` | `Boolean` | 是否可分配 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 26. `ticket`

用途: 工单。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String(36)` | 主键 |
| `conversation_id` | `String(36)?` | 关联会话 ID |
| `department_id` | `String(36)?` | 所属部门 ID |
| `assigned_to_id` | `String(36)?` | 分配给成员 ID |
| `title` | `String(500)` | 工单标题 |
| `description` | `Text` | 工单描述 |
| `status` | `String(50)` | 工单状态 |
| `priority` | `String(50)` | 工单优先级 |
| `resolution` | `Text` | 处理结果/解决方案 |
| `created_at` | `DateTime` | 创建时间 |
| `updated_at` | `DateTime` | 更新时间 |

## 27. 当前 Python 模型中未实现的 TS 表

当前这一轮补齐后，TS Prisma schema 中的核心表在 Python SQLAlchemy models 里都已经有对应模型。
