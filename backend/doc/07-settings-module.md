# Settings 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中设置模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/app/api/settings/
└── route.ts              # 设置 CRUD
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── settings.py       # 设置 API 端点
├── domain/settings/
│   └── service.py        # 设置服务
└── infrastructure/db/
    ├── models/operations.py  # Settings 模型
    └── repositories/settings.py
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 获取设置 | ✅ GET /api/settings | ✅ GET /api/v1/settings | ✅ 一致 |
| 更新设置 | ✅ PUT /api/settings | ✅ PUT /api/v1/settings | ✅ 一致 |
| 敏感字段隐藏 | ✅ | ✅ | ✅ 一致 |

## 3. 核心代码对比

### 3.1 获取设置

**TypeScript (`src/app/api/settings/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "settings:read");
  if (!isAuthenticated(auth)) return auth;

  const settings = await prisma.settings.findUnique({
    where: { id: "default" },
  });

  if (!settings) {
    return NextResponse.json({ error: "Settings not found" }, { status: 404 });
  }

  // 隐藏敏感字段
  const { aiApiKey, smtpPass, imapPass, twilioToken, elevenLabsKey, whatsappApiKey, telegramBotToken, ...safeSettings } = settings;

  return NextResponse.json(safeSettings);
}
```

**Python (`backend/app/api/v1/settings.py`):**
```python
SENSITIVE_FIELDS = [
    "ai_api_key", "smtp_pass", "imap_pass", "twilio_token",
    "eleven_labs_key", "whatsapp_api_key", "telegram_bot_token"
]

@router.get("")
async def get_settings(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    settings = await session.get(Settings, "default")
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    data = {
        column.name: getattr(settings, column.name)
        for column in settings.__table__.columns
    }
    for field in SENSITIVE_FIELDS:
        if field in data and data[field]:
            data[field] = "••••••••"

    return data
```

### 3.2 更新设置

**TypeScript:**
```typescript
export async function PUT(request: NextRequest) {
  const auth = await requireAuth(request, "settings:update");
  if (!isAuthenticated(auth)) return auth;

  const body = await request.json();

  // 过滤只读字段
  const { id, createdAt, updatedAt, ...updateData } = body;

  const settings = await prisma.settings.update({
    where: { id: "default" },
    data: updateData,
  });

  const { aiApiKey, smtpPass, ...safeSettings } = settings;
  return NextResponse.json(safeSettings);
}
```

**Python:**
```python
READONLY_FIELDS = ["id", "created_at", "updated_at"]

@router.put("")
async def update_settings(
    payload: dict[str, Any],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    settings = await session.get(Settings, "default")
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    for key, value in payload.items():
        if key not in READONLY_FIELDS and hasattr(settings, key):
            setattr(settings, key, value)

    await session.commit()
    await session.refresh(settings)

    # 返回时隐藏敏感字段
    ...
```

## 4. 数据模型对比

**TypeScript (Prisma):**
```prisma
model Settings {
  id              String   @id @default("default")
  businessName    String   @default("My Business")
  businessDesc    String?
  welcomeMessage  String?
  tone            String   @default("friendly")
  language        String   @default("auto")
  aiProvider      String   @default("openai")
  aiModel         String   @default("gpt-4o-mini")
  aiApiKey        String?
  maxTokens       Int      @default(2048)
  temperature     Float    @default(0.7)
  smtpHost        String?
  smtpPort        Int      @default(587)
  smtpUser        String?
  smtpPass        String?
  smtpFrom        String?
  imapHost        String?
  imapPort        Int      @default(993)
  imapUser        String?
  imapPass        String?
  twilioSid       String?
  twilioToken     String?
  twilioPhone     String?
  elevenLabsKey   String?
  elevenLabsVoice String?
  whatsappMode    String   @default("web")
  whatsappApiKey  String?
  whatsappPhone   String?
  telegramBotToken String?
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    business_name: Mapped[str] = mapped_column(String(500), default="My Business")
    business_desc: Mapped[str] = mapped_column(String(5000), default="")
    welcome_message: Mapped[str] = mapped_column(String(2000), default="Hello! How can I help you today?")
    tone: Mapped[str] = mapped_column(String(50), default="friendly")
    language: Mapped[str] = mapped_column(String(20), default="auto")
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    ai_api_key: Mapped[str] = mapped_column(String(500), default="")
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    smtp_host: Mapped[str] = mapped_column(String(500), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(300), default="")
    smtp_pass: Mapped[str] = mapped_column(String(500), default="")
    smtp_from: Mapped[str] = mapped_column(String(300), default="")
    imap_host: Mapped[str] = mapped_column(String(500), default="")
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_user: Mapped[str] = mapped_column(String(300), default="")
    imap_pass: Mapped[str] = mapped_column(String(500), default="")
    twilio_sid: Mapped[str] = mapped_column(String(200), default="")
    twilio_token: Mapped[str] = mapped_column(String(200), default="")
    twilio_phone: Mapped[str] = mapped_column(String(50), default="")
    eleven_labs_key: Mapped[str] = mapped_column(String(200), default="")
    eleven_labs_voice: Mapped[str] = mapped_column(String(200), default="")
    whatsapp_mode: Mapped[str] = mapped_column(String(50), default="web")
    whatsapp_api_key: Mapped[str] = mapped_column(String(500), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(50), default="")
    telegram_bot_token: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

## 5. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 单例模式 | id="default" | id="default" |
| 敏感字段处理 | 解构排除 | 列表遍历遮蔽 |
| 只读字段保护 | 解构排除 | 列表过滤 |

Python 版本功能与 TypeScript 版本完全一致。
