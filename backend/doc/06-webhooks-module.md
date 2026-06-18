# Webhooks 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中 Webhook 模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/
├── lib/
│   └── webhook-delivery.ts     # Webhook 投递逻辑
├── app/api/webhooks/
│   ├── route.ts                # Webhook 列表/创建
│   ├── [id]/
│   │   ├── route.ts            # Webhook CRUD
│   │   └── deliveries/route.ts # 投递记录
│   └── test/route.ts           # Webhook 测试
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── webhooks.py             # Webhook API 端点
├── infrastructure/webhooks/
│   └── delivery.py             # Webhook 投递服务
└── infrastructure/db/
    └── models/operations.py    # Webhook, WebhookDelivery 模型
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| Webhook 列表 | ✅ GET /api/webhooks | ✅ GET /api/v1/webhooks | ✅ 一致 |
| 创建 Webhook | ✅ POST /api/webhooks | ✅ POST /api/v1/webhooks | ✅ 一致 |
| Webhook CRUD | ✅ | ✅ | ✅ 一致 |
| 投递记录 | ✅ GET /[id]/deliveries | ✅ GET /{id}/deliveries | ✅ 一致 |
| Webhook 测试 | ✅ POST /test | ✅ POST /test | ✅ 一致 |
| HMAC 签名 | ✅ | ✅ | ✅ 一致 |
| 重试机制 | ✅ setTimeout | ✅ 可配置 | ✅ 一致 |
| 投递追踪 | ✅ | ✅ | ✅ 一致 |

## 3. 核心代码对比

### 3.1 HMAC 签名生成

**TypeScript (`src/lib/webhook-delivery.ts`):**
```typescript
import crypto from "crypto";

export function generateSignature(payload: string, secret: string): string {
  return crypto.createHmac("sha256", secret).update(payload).digest("hex");
}
```

**Python (`backend/app/infrastructure/webhooks/delivery.py`):**
```python
import hashlib
import hmac

def generate_signature(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
```

**差异分析:**
- 两者都使用 HMAC-SHA256 算法
- TypeScript 使用 Node.js crypto 模块
- Python 使用标准库 hmac + hashlib

### 3.2 Webhook 投递

**TypeScript:**
```typescript
const MAX_ATTEMPTS = 3;
const RETRY_DELAYS = [5000, 30000, 300000]; // 5s, 30s, 5min
const DELIVERY_TIMEOUT = 10000;

export async function deliverWebhook(
  webhook: WebhookConfig,
  event: string,
  data: Record<string, unknown>
): Promise<{ deliveryId: string; success: boolean }> {
  const payload = JSON.stringify({
    event,
    timestamp: new Date().toISOString(),
    webhookId: webhook.id,
    data,
  });

  const delivery = await prisma.webhookDelivery.create({
    data: {
      webhookId: webhook.id,
      event,
      payload: JSON.parse(payload),
      status: "pending",
      attempts: 0,
    },
  });

  const result = await attemptDelivery(webhook, payload, delivery.id);
  return { deliveryId: delivery.id, success: result };
}

async function attemptDelivery(
  webhook: WebhookConfig,
  payload: string,
  deliveryId: string,
  attempt = 1
): Promise<boolean> {
  const webhookSecret = process.env.WEBHOOK_SECRET || "";
  const signature = webhookSecret ? generateSignature(payload, webhookSecret) : "";

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DELIVERY_TIMEOUT);

  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "User-Agent": "Owly-Webhook/1.0",
      ...webhook.headers,
    };

    if (signature) {
      headers["X-Owly-Signature"] = signature;
    }

    const response = await fetch(webhook.url, {
      method: webhook.method,
      headers,
      body: webhook.method !== "GET" ? payload : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      await prisma.webhookDelivery.update({
        where: { id: deliveryId },
        data: { status: "delivered", statusCode: response.status, attempts: attempt },
      });
      return true;
    }

    throw new Error(`HTTP ${response.status}`);
  } catch (error) {
    clearTimeout(timeoutId);

    if (attempt < MAX_ATTEMPTS) {
      const retryDelay = RETRY_DELAYS[attempt - 1];
      const nextRetryAt = new Date(Date.now() + retryDelay);

      await prisma.webhookDelivery.update({
        where: { id: deliveryId },
        data: { status: "pending", attempts: attempt, lastError: error.message, nextRetryAt },
      });

      setTimeout(() => {
        attemptDelivery(webhook, payload, deliveryId, attempt + 1).catch(console.error);
      }, retryDelay);

      return false;
    }

    await prisma.webhookDelivery.update({
      where: { id: deliveryId },
      data: { status: "failed", attempts: attempt, lastError: error.message },
    });

    return false;
  }
}
```

**Python:**
```python
MAX_ATTEMPTS = 3
RETRY_DELAYS = [5, 30, 300]  # 秒
DELIVERY_TIMEOUT = 10.0

class WebhookDeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def deliver_webhook(
        self, webhook: Webhook, event: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        payload_dict = {
            "event": event,
            "timestamp": datetime.now(UTC).isoformat(),
            "webhookId": webhook.id,
            "data": data,
        }
        payload = json.dumps(payload_dict)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload_dict,
            status="pending",
            attempts=0,
        )
        self.session.add(delivery)
        await self.session.commit()
        await self.session.refresh(delivery)

        success = await self._attempt_delivery(webhook, payload, delivery.id, attempt=1)
        return {"deliveryId": delivery.id, "success": success}

    async def _attempt_delivery(
        self, webhook: Webhook, payload: str, delivery_id: str, attempt: int = 1
    ) -> bool:
        webhook_secret = getattr(self.settings, "webhook_secret", "") or ""
        signature = generate_signature(payload, webhook_secret) if webhook_secret else ""

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "Owly-Webhook/1.0",
            **(webhook.headers or {}),
        }
        if signature:
            headers["X-Owly-Signature"] = signature

        delivery = await self.session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return False

        try:
            async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT) as client:
                response = await client.request(
                    method=webhook.method,
                    url=webhook.url,
                    headers=headers,
                    content=payload if webhook.method != "GET" else None,
                )

            if response.is_success:
                delivery.status = "delivered"
                delivery.status_code = response.status_code
                delivery.attempts = attempt
                await self.session.commit()
                return True

            error_message = f"HTTP {response.status_code}: {response.text}"

        except httpx.TimeoutException:
            error_message = "Request timed out"
        except Exception as e:
            error_message = str(e)

        if attempt < MAX_ATTEMPTS:
            retry_delay = RETRY_DELAYS[attempt - 1]
            next_retry_at = datetime.now(UTC) + timedelta(seconds=retry_delay)

            delivery.status = "pending"
            delivery.attempts = attempt
            delivery.last_error = error_message
            delivery.next_retry_at = next_retry_at
            await self.session.commit()

            return False

        delivery.status = "failed"
        delivery.attempts = attempt
        delivery.last_error = error_message
        await self.session.commit()

        return False
```

### 3.3 重试机制对比

**TypeScript:**
- 使用 `setTimeout` 进行异步重试
- 重试延迟：5秒、30秒、5分钟
- 最大尝试次数：3次

**Python:**
- 使用 `next_retry_at` 字段记录下次重试时间
- 需要外部调度器（如 Celery 或定时任务）来处理重试
- 相同的重试延迟和最大尝试次数

## 4. 数据模型对比

### Webhook 模型

**TypeScript (Prisma):**
```prisma
model Webhook {
  id          String   @id @default(cuid())
  name        String
  description String?
  url         String
  method      String   @default("POST")
  headers     Json?
  isActive    Boolean  @default(true)
  triggerOn   String
  deliveries  WebhookDelivery[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Webhook(Base):
    __tablename__ = "webhook"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000))
    url: Mapped[str] = mapped_column(String(2000))
    method: Mapped[str] = mapped_column(String(10), default="POST")
    headers: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trigger_on: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

### WebhookDelivery 模型

**TypeScript (Prisma):**
```prisma
model WebhookDelivery {
  id          String    @id @default(cuid())
  webhookId   String
  webhook     Webhook   @relation(fields: [webhookId], references: [id])
  event       String
  payload     Json
  status      String    @default("pending")
  statusCode  Int?
  attempts    Int       @default(0)
  lastError   String?
  nextRetryAt DateTime?
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt

  @@index([status])
}
```

**Python (SQLAlchemy):**
```python
class WebhookDelivery(Base):
    __tablename__ = "webhook_delivery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    webhook_id: Mapped[str] = mapped_column(ForeignKey("webhook.id", ondelete="CASCADE"), index=True)
    event: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    status_code: Mapped[int | None] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    next_retry_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

## 5. API 端点对比

| 方法 | TypeScript | Python |
|------|------------|--------|
| GET | `/api/webhooks` | `/api/v1/webhooks` |
| POST | `/api/webhooks` | `/api/v1/webhooks` |
| GET | `/api/webhooks/[id]` | `/api/v1/webhooks/{id}` |
| PUT | `/api/webhooks/[id]` | `/api/v1/webhooks/{id}` |
| DELETE | `/api/webhooks/[id]` | `/api/v1/webhooks/{id}` |
| GET | `/api/webhooks/[id]/deliveries` | `/api/v1/webhooks/{id}/deliveries` |
| POST | `/api/webhooks/test` | `/api/v1/webhooks/test` |

## 6. 工作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Webhook 投递流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 触发事件                                                     │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ conversation:created, message:received, etc.          │  │
│     └───────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  2. 查找匹配的 Webhook                                           │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ SELECT * FROM webhook WHERE trigger_on LIKE '%event%' │  │
│     └───────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  3. 创建投递记录                                                 │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ INSERT INTO webhook_delivery (status: 'pending')      │  │
│     └───────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  4. 发送 HTTP 请求                                               │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ POST {webhook.url}                                    │  │
│     │ Headers: X-Owly-Signature: {hmac_sha256}              │  │
│     └───────────────────────────────────────────────────────┘  │
│                           │                                     │
│              ┌────────────┴────────────┐                       │
│              ▼                         ▼                       │
│         成功 (2xx)                  失败/超时                   │
│              │                         │                       │
│              ▼                         ▼                       │
│     更新状态: delivered         尝试次数 < 3?                   │
│                                        │                       │
│                              ┌─────────┴─────────┐             │
│                              ▼                   ▼             │
│                           是 (重试)          否 (失败)          │
│                              │                   │             │
│                              ▼                   ▼             │
│                    设置 next_retry_at    更新状态: failed       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 7. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| HTTP 客户端 | fetch (原生) | httpx |
| 签名算法 | HMAC-SHA256 | HMAC-SHA256 |
| 重试机制 | setTimeout | next_retry_at + 调度器 |
| 超时控制 | AbortController | httpx timeout |
| 投递追踪 | ✅ | ✅ |

Python 版本功能与 TypeScript 版本一致，重试机制需要配合外部调度器使用。
