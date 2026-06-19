# 渠道模块 Channels

## 业务流程

1. 管理员保存渠道配置，如 email、WhatsApp、phone、telegram。
2. 渠道配置写入 `channel.config`，连接状态写入 `channel.status`。
3. 管理员执行连接、断开或测试动作。
4. 外部渠道回调进入专用 API，例如电话来电、语音输入、通话状态。
5. 电话回调可创建或更新会话，产生客户消息，并返回 TwiML 语音响应。
6. 邮件/WhatsApp 等渠道可作为会话来源，也可被 AI 外联使用。

## 领域对象与关系

- `Channel`：渠道配置和状态。
- `CallLog`：电话通话记录。
- `Conversation`：渠道消息最终进入客服会话。
- `ChannelService`：渠道配置管理。
- `ConversationService`：渠道回调用于创建会话/消息。

关系说明：

- `Channel` 和 `CallLog` 当前没有数据库外键。
- `CallLog.call_sid` 与外部电话平台通话记录对应。
- 渠道回调会在业务上关联或创建 `conversation`、`message`。

## 状态机

### 渠道连接状态

```text
disconnected
  ├─ connect 成功 -> connected
  ├─ connect 失败 -> error
  └─ test -> disconnected
connected
  ├─ disconnect -> disconnected
  ├─ test 成功 -> connected
  └─ 外部异常 -> error
error
  ├─ reconnect 成功 -> connected
  └─ disconnect -> disconnected
```

### 电话通话状态

```text
initiated
  ├─ ringing -> in_progress
  ├─ completed -> completed
  └─ failed/busy/no_answer -> failed
```

## 模块结构

- `backend/app/api/v1/channels.py`：渠道 API 和外部回调。
- `backend/app/domain/channels/service.py`：渠道配置服务。
- `backend/app/domain/channels/schemas.py`：渠道 schema。
- `backend/app/infrastructure/db/models/operations.py`：`Channel`、`CallLog`。
- `backend/app/infrastructure/db/repositories/channels.py`：渠道仓储。
- `backend/app/infrastructure/integrations/channels.py`：外部渠道集成抽象。
