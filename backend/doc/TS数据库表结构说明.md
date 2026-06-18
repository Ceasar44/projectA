# TS 代码数据库表结构说明

来源: `prisma/schema.prisma`

说明:

- 本文件描述的是原 TS 代码使用的 Prisma 数据模型。
- 字段名保持 TS/Prisma 原始命名风格。
- 含义说明尽量简短，便于快速查阅。

## 1. `Settings`

用途: 系统全局配置，通常只有一条默认记录。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键，默认是 `default` |
| `businessName` | `String` | 企业名称 |
| `businessDesc` | `String` | 企业描述 |
| `welcomeMessage` | `String` | 默认欢迎语 |
| `tone` | `String` | AI 回复语气 |
| `language` | `String` | 回复语言设置 |
| `aiProvider` | `String` | AI 服务提供商 |
| `aiModel` | `String` | AI 模型名称 |
| `aiApiKey` | `String` | AI API 密钥 |
| `maxTokens` | `Int` | AI 最大输出 token 数 |
| `temperature` | `Float` | AI 采样温度 |
| `elevenLabsKey` | `String` | ElevenLabs API Key |
| `elevenLabsVoice` | `String` | ElevenLabs 音色配置 |
| `twilioSid` | `String` | Twilio SID |
| `twilioToken` | `String` | Twilio Token |
| `twilioPhone` | `String` | Twilio 电话号码 |
| `smtpHost` | `String` | SMTP 主机 |
| `smtpPort` | `Int` | SMTP 端口 |
| `smtpUser` | `String` | SMTP 用户名 |
| `smtpPass` | `String` | SMTP 密码 |
| `smtpFrom` | `String` | 发件人地址 |
| `imapHost` | `String` | IMAP 主机 |
| `imapPort` | `Int` | IMAP 端口 |
| `imapUser` | `String` | IMAP 用户名 |
| `imapPass` | `String` | IMAP 密码 |
| `whatsappMode` | `String` | WhatsApp 接入模式 |
| `whatsappApiKey` | `String` | WhatsApp API Key |
| `whatsappPhone` | `String` | WhatsApp 号码 |
| `telegramBotToken` | `String` | Telegram Bot Token |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 2. `Admin`

用途: 管理后台账号。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `username` | `String` | 登录用户名 |
| `password` | `String` | 哈希后的密码 |
| `name` | `String` | 显示名称 |
| `role` | `String` | 角色 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 3. `Category`

用途: 知识库分类。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 分类名称 |
| `description` | `String` | 分类描述 |
| `icon` | `String` | 分类图标 |
| `color` | `String` | 分类颜色 |
| `sortOrder` | `Int` | 排序值 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 4. `KnowledgeEntry`

用途: 知识库条目。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `categoryId` | `String` | 所属分类 ID |
| `title` | `String` | 条目标题 |
| `content` | `String` | 条目正文 |
| `priority` | `Int` | 优先级 |
| `isActive` | `Boolean` | 是否启用 |
| `version` | `Int` | 版本号 |
| `metadata` | `Json` | 扩展元数据 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 5. `Department`

用途: 团队部门。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 部门名称 |
| `description` | `String` | 部门描述 |
| `email` | `String` | 部门邮箱 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 6. `TeamMember`

用途: 团队成员/坐席。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 成员姓名 |
| `email` | `String` | 成员邮箱 |
| `phone` | `String` | 成员电话 |
| `role` | `String` | 成员角色 |
| `expertise` | `String` | 专长领域 |
| `departmentId` | `String` | 所属部门 ID |
| `isAvailable` | `Boolean` | 是否可分配 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 7. `Conversation`

用途: 客户会话主表。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `channel` | `String` | 渠道类型 |
| `customerName` | `String` | 客户姓名 |
| `customerContact` | `String` | 客户联系方式 |
| `customerId` | `String?` | 关联客户 ID |
| `status` | `String` | 会话状态 |
| `satisfaction` | `Int?` | 满意度评分 |
| `summary` | `String` | 会话摘要 |
| `metadata` | `Json` | 会话扩展元数据 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 8. `Message`

用途: 会话消息。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `conversationId` | `String` | 所属会话 ID |
| `role` | `String` | 消息角色，如 customer/assistant |
| `content` | `String` | 消息内容 |
| `mediaType` | `String?` | 媒体类型 |
| `mediaUrl` | `String?` | 媒体地址 |
| `toolCalls` | `Json?` | AI 工具调用信息 |
| `createdAt` | `DateTime` | 创建时间 |

## 9. `Ticket`

用途: 工单。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `conversationId` | `String?` | 关联会话 ID |
| `departmentId` | `String?` | 所属部门 ID |
| `assignedToId` | `String?` | 分配给成员 ID |
| `title` | `String` | 工单标题 |
| `description` | `String` | 工单描述 |
| `status` | `String` | 工单状态 |
| `priority` | `String` | 工单优先级 |
| `resolution` | `String` | 处理结果/解决方案 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 10. `Tag`

用途: 会话标签定义。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 标签名称 |
| `color` | `String` | 标签颜色 |
| `createdAt` | `DateTime` | 创建时间 |

## 11. `ConversationTag`

用途: 会话与标签的关联表。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `conversationId` | `String` | 会话 ID |
| `tagId` | `String` | 标签 ID |

## 12. `CallLog`

用途: 电话呼叫记录。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `callSid` | `String` | Twilio 呼叫唯一标识 |
| `from` | `String` | 来电号码 |
| `to` | `String` | 目标号码 |
| `duration` | `Int` | 通话时长 |
| `status` | `String` | 通话状态 |
| `recording` | `String?` | 录音地址 |
| `summary` | `String` | 通话摘要 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 13. `Channel`

用途: 渠道接入配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `type` | `String` | 渠道类型 |
| `isActive` | `Boolean` | 是否启用 |
| `config` | `Json` | 渠道配置 |
| `status` | `String` | 渠道状态 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 14. `Schedule`

用途: 团队排班。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `teamMemberId` | `String` | 团队成员 ID |
| `dayOfWeek` | `Int` | 星期几 |
| `startTime` | `String` | 开始时间 |
| `endTime` | `String` | 结束时间 |

## 15. `Webhook`

用途: 外部 Webhook 配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | Webhook 名称 |
| `description` | `String` | Webhook 描述 |
| `url` | `String` | 目标地址 |
| `method` | `String` | 请求方法 |
| `headers` | `Json` | 自定义请求头 |
| `isActive` | `Boolean` | 是否启用 |
| `triggerOn` | `String` | 触发事件 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 16. `WebhookDelivery`

用途: Webhook 投递记录。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `webhookId` | `String` | Webhook ID |
| `event` | `String` | 事件名称 |
| `payload` | `Json` | 投递载荷 |
| `status` | `String` | 投递状态 |
| `statusCode` | `Int?` | HTTP 状态码 |
| `attempts` | `Int` | 重试次数 |
| `lastError` | `String?` | 最近错误信息 |
| `nextRetryAt` | `DateTime?` | 下次重试时间 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 17. `ActivityLog`

用途: 操作审计日志。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `action` | `String` | 动作名称 |
| `entity` | `String` | 实体类型 |
| `entityId` | `String?` | 实体 ID |
| `description` | `String` | 描述信息 |
| `userId` | `String?` | 操作人 ID |
| `userName` | `String` | 操作人名称 |
| `metadata` | `Json` | 扩展元数据 |
| `requestId` | `String?` | 请求 ID |
| `ipAddress` | `String?` | IP 地址 |
| `userAgent` | `String?` | User-Agent |
| `createdAt` | `DateTime` | 创建时间 |

## 18. `SLARule`

用途: SLA 规则。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 规则名称 |
| `description` | `String` | 规则描述 |
| `channel` | `String` | 适用渠道 |
| `priority` | `String` | 适用优先级 |
| `firstResponseMins` | `Int` | 首次响应时限 |
| `resolutionMins` | `Int` | 解决时限 |
| `isActive` | `Boolean` | 是否启用 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 19. `CannedResponse`

用途: 快捷回复模板。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `title` | `String` | 模板标题 |
| `content` | `String` | 模板内容 |
| `category` | `String` | 模板分类 |
| `shortcut` | `String` | 快捷命令 |
| `isActive` | `Boolean` | 是否启用 |
| `usageCount` | `Int` | 使用次数 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 20. `Customer`

用途: 客户主档案。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 客户姓名 |
| `email` | `String` | 邮箱 |
| `phone` | `String` | 电话 |
| `whatsapp` | `String` | WhatsApp 联系方式 |
| `tags` | `String` | 标签字符串 |
| `isBlocked` | `Boolean` | 是否封禁 |
| `metadata` | `Json` | 扩展元数据 |
| `firstContact` | `DateTime` | 首次联系时间 |
| `lastContact` | `DateTime` | 最近联系时间 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 21. `CustomerNote`

用途: 客户备注。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `customerId` | `String` | 客户 ID |
| `content` | `String` | 备注内容 |
| `authorName` | `String` | 作者名称 |
| `createdAt` | `DateTime` | 创建时间 |

## 22. `AutomationRule`

用途: 自动化规则。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 规则名称 |
| `description` | `String` | 规则描述 |
| `type` | `String` | 规则类型 |
| `isActive` | `Boolean` | 是否启用 |
| `conditions` | `Json` | 触发条件 |
| `actions` | `Json` | 执行动作 |
| `priority` | `Int` | 优先级 |
| `triggerCount` | `Int` | 触发次数 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 23. `BusinessHours`

用途: 营业时间配置。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键，默认 `default` |
| `enabled` | `Boolean` | 是否启用营业时间 |
| `timezone` | `String` | 时区 |
| `monday` | `String` | 周一营业时间 |
| `tuesday` | `String` | 周二营业时间 |
| `wednesday` | `String` | 周三营业时间 |
| `thursday` | `String` | 周四营业时间 |
| `friday` | `String` | 周五营业时间 |
| `saturday` | `String` | 周六营业时间 |
| `sunday` | `String` | 周日营业时间 |
| `offlineMessage` | `String` | 非营业时间提示语 |

## 24. `ApiKey`

用途: 外部 API 访问密钥。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | Key 名称 |
| `key` | `String` | 实际密钥 |
| `isActive` | `Boolean` | 是否启用 |
| `lastUsed` | `DateTime?` | 上次使用时间 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 25. `InternalNote`

用途: 会话内部备注。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `conversationId` | `String` | 会话 ID |
| `content` | `String` | 备注内容 |
| `authorName` | `String` | 作者名称 |
| `createdAt` | `DateTime` | 创建时间 |

## 26. `Campaign`

用途: 主动营销/触达活动。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 活动名称 |
| `description` | `String` | 活动描述 |
| `channel` | `String` | 发送渠道 |
| `message` | `String` | 消息正文 |
| `subject` | `String` | 邮件主题 |
| `segments` | `Json` | 客群筛选条件 |
| `status` | `String` | 活动状态 |
| `scheduledAt` | `DateTime?` | 计划执行时间 |
| `sentCount` | `Int` | 已发送数量 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

## 27. `Flow`

用途: 对话流程编排定义。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | `String` | 主键 |
| `name` | `String` | 流程名称 |
| `description` | `String` | 流程描述 |
| `startNodeId` | `String` | 起始节点 ID |
| `nodes` | `Json` | 节点定义集合 |
| `isActive` | `Boolean` | 是否启用 |
| `triggerCount` | `Int` | 触发次数 |
| `createdAt` | `DateTime` | 创建时间 |
| `updatedAt` | `DateTime` | 更新时间 |

