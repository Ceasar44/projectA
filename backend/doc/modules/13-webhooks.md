# Webhook 模块 Webhooks

## 业务流程

1. 管理员创建 Webhook，配置名称、URL、HTTP 方法、请求头和触发事件。
2. 业务事件发生时，系统根据 `trigger_on` 找到启用的 Webhook。
3. 系统创建 `webhook_delivery` 投递记录，并向目标 URL 发送请求。
4. 投递成功后记录状态码和成功状态。
5. 投递失败时记录错误、尝试次数和下次重试时间。
6. 管理员可查看投递记录，并手动重试。

## 领域对象与关系

- `Webhook`：Webhook 配置。
- `WebhookDelivery`：投递记录。
- `WebhookService`：Webhook CRUD、测试和重试服务。
- `WebhookDeliveryRunner`：实际投递执行器。

关系说明：

- `webhook.id` 1 对多 `webhook_delivery.webhook_id`。
- 删除 Webhook 时，投递记录级联删除。
- `payload` 保存投递事件快照，不强依赖原业务表。

## 状态机

### Webhook 启用状态

```text
inactive
  └─ is_active=true -> active
active
  └─ is_active=false -> inactive
```

### 投递状态

```text
pending
  ├─ 发送成功 -> success
  ├─ 发送失败但可重试 -> retrying
  └─ 发送失败且超过限制 -> failed
retrying
  ├─ retry 成功 -> success
  └─ retry 失败 -> retrying/failed
failed
  └─ 手动 retry -> retrying
```

## 模块结构

- `backend/app/api/v1/webhooks.py`：Webhook API。
- `backend/app/domain/webhooks/service.py`：Webhook 业务服务。
- `backend/app/domain/webhooks/schemas.py`：Webhook schema。
- `backend/app/infrastructure/db/models/operations.py`：`Webhook`、`WebhookDelivery`。
- `backend/app/infrastructure/db/repositories/webhooks.py`：Webhook 仓储。
- `backend/app/infrastructure/webhooks/delivery.py`：投递执行逻辑。
