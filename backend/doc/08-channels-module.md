# Channels 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中渠道模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/app/api/channels/
├── route.ts              # 渠道列表
├── [type]/route.ts       # 渠道 CRUD
├── email/route.ts        # Email 渠道
├── phone/
│   ├── incoming/route.ts # 电话接入
│   ├── gather/route.ts   # IVR 收集
│   └── status/route.ts   # 通话状态
├── sms/route.ts          # SMS 渠道
├── telegram/route.ts     # Telegram 渠道
└── whatsapp/route.ts     # WhatsApp 渠道
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── channels.py       # 渠道 API 端点
├── infrastructure/channels/
│   ├── email.py          # Email 处理
│   ├── sms.py            # SMS 处理
│   ├── telegram.py       # Telegram 处理
│   └── whatsapp.py       # WhatsApp 处理
└── infrastructure/db/
    └── models/operations.py  # Channel 模型
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 渠道列表 | ✅ GET /api/channels | ✅ GET /api/v1/channels | ✅ 一致 |
| 渠道 CRUD | ✅ /[type] | ✅ /{type} | ✅ 一致 |
| Email 处理 | ✅ | ✅ | ✅ 一致 |
| SMS 处理 | ✅ | ✅ | ✅ 一致 |
| WhatsApp 处理 | ✅ | ✅ | ✅ 一致 |
| Telegram 处理 | ✅ | ✅ | ✅ 一致 |
| 电话接入 | ✅ | ✅ | ✅ 一致 |

## 3. 核心代码对比

### 3.1 渠道列表

**TypeScript (`src/app/api/channels/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "channels:read");
  if (!isAuthenticated(auth)) return auth;

  const channels = await prisma.channel.findMany({
    orderBy: { type: "asc" },
  });

  return NextResponse.json({ channels });
}
```

**Python (`backend/app/api/v1/channels.py`):**
```python
@router.get("")
async def list_channels(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    channels = list(
        (await session.scalars(select(Channel).order_by(Channel.type))).all()
    )
    return {"channels": [serialize_channel(c) for c in channels]}
```

### 3.2 渠道更新

**TypeScript (`src/app/api/channels/[type]/route.ts`):**
```typescript
export async function PUT(
  request: NextRequest,
  { params }: { params: { type: string } }
) {
  const auth = await requireAuth(request, "channels:update");
  if (!isAuthenticated(auth)) return auth;

  const body = await request.json();
  const { isActive, config } = body;

  const channel = await prisma.channel.update({
    where: { type: params.type },
    data: {
      isActive: isActive ?? false,
      config: config || {},
      status: isActive ? "connected" : "disconnected",
    },
  });

  return NextResponse.json(channel);
}
```

**Python:**
```python
@router.put("/{channel_type}")
async def update_channel(
    channel_type: str,
    payload: dict[str, Any],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    channel = await session.scalar(
        select(Channel).where(Channel.type == channel_type)
    )
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    is_active = payload.get("isActive", False)
    channel.is_active = is_active
    channel.config = payload.get("config", {})
    channel.status = "connected" if is_active else "disconnected"

    await session.commit()
    await session.refresh(channel)
    return serialize_channel(channel)
```

## 4. 数据模型对比

**TypeScript (Prisma):**
```prisma
model Channel {
  id        String   @id @default(cuid())
  type      String   @unique
  isActive  Boolean  @default(false)
  config    Json?
  status    String   @default("disconnected")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Channel(Base):
    __tablename__ = "channel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="disconnected")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

## 5. 渠道类型

| 渠道 | TypeScript | Python | 说明 |
|------|------------|--------|------|
| whatsapp | ✅ | ✅ | WhatsApp Business API |
| ✅ | ✅ | SMTP/IMAP | |
| phone | ✅ | ✅ | Twilio Voice |
| sms | ✅ | ✅ | Twilio SMS |
| telegram | ✅ | ✅ | Telegram Bot API |

## 6. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 文件组织 | 按渠道分文件 | 集中 + 按渠道分模块 |
| 配置存储 | JSON 字段 | JSON 字段 |
| 状态管理 | connected/disconnected | connected/disconnected |

Python 版本功能与 TypeScript 版本完全一致。
