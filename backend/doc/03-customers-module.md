# Customers 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中客户模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/
├── lib/
│   ├── gdpr.ts                  # GDPR 合规工具
│   └── customer-resolver.ts     # 客户解析
├── app/api/customers/
│   ├── route.ts                 # 列表/创建
│   └── [id]/
│       ├── route.ts             # 获取/更新/删除
│       ├── notes/route.ts       # 笔记管理
│       ├── conversations/route.ts # 对话列表
│       └── gdpr/
│           ├── export/route.ts  # 数据导出
│           └── delete/route.ts  # 数据删除
```

### Python (backend) 架构

```
backend/app/
├── domain/
│   ├── customer/
│   │   ├── schemas.py           # 数据模型
│   │   └── service.py           # 业务逻辑
│   └── gdpr/
│       └── service.py           # GDPR 服务
├── api/v1/
│   └── customers.py             # 所有端点
└── infrastructure/db/
    ├── models/conversations.py  # Customer 模型
    └── repositories/customers.py
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 客户列表 | ✅ GET /api/customers | ✅ GET /api/v1/customers | ✅ 一致 |
| 创建客户 | ✅ POST /api/customers | ✅ POST /api/v1/customers | ✅ 一致 |
| 获取客户 | ✅ GET /api/customers/[id] | ✅ GET /api/v1/customers/{id} | ✅ 一致 |
| 更新客户 | ✅ PUT /api/customers/[id] | ✅ PUT /api/v1/customers/{id} | ✅ 一致 |
| 删除客户 | ✅ DELETE /api/customers/[id] | ✅ DELETE /api/v1/customers/{id} | ✅ 一致 |
| 客户笔记 | ✅ GET/POST /[id]/notes | ✅ GET/POST /{id}/notes | ✅ 一致 |
| 客户对话 | ✅ GET /[id]/conversations | ✅ GET /{id}/conversations | ✅ 一致 |
| GDPR 导出 | ✅ GET /[id]/gdpr/export | ✅ GET /{id}/gdpr/export | ✅ 一致 |
| GDPR 删除 | ✅ DELETE /[id]/gdpr/delete | ✅ DELETE /{id}/gdpr/delete | ✅ 一致 |
| PII 脱敏 | ❌ | ✅ redact_pii() | 🆕 增强 |
| 数据保留策略 | ❌ | ✅ apply_retention_policy() | 🆕 增强 |

## 3. 核心代码对比

### 3.1 客户列表

**TypeScript (`src/app/api/customers/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "customers:read");
  if (!isAuthenticated(auth)) return auth;

  const { searchParams } = new URL(request.url);
  const { page, limit, skip, take } = parsePagination(searchParams);
  const search = searchParams.get("search");
  const isBlocked = searchParams.get("isBlocked");

  const where: Record<string, unknown> = {};

  if (search && search.trim()) {
    where.OR = [
      { name: { contains: search.trim(), mode: "insensitive" } },
      { email: { contains: search.trim(), mode: "insensitive" } },
      { phone: { contains: search.trim(), mode: "insensitive" } },
    ];
  }

  if (isBlocked === "true") {
    where.isBlocked = true;
  }

  const [customers, total] = await Promise.all([
    prisma.customer.findMany({
      where,
      orderBy: { lastContact: "desc" },
      skip,
      take,
      include: { _count: { select: { notes: true } } },
    }),
    prisma.customer.count({ where }),
  ]);

  return NextResponse.json(paginatedResponse(customers, total, page, limit));
}
```

**Python (`backend/app/api/v1/customers.py`):**
```python
@router.get("")
async def list_customers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    is_blocked: bool | None = Query(default=None, alias="isBlocked"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    filters = []
    if search:
        like = f"%{search}%"
        filters.append(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
                Customer.whatsapp.ilike(like),
            )
        )
    if is_blocked is not None:
        filters.append(Customer.is_blocked == is_blocked)

    stmt = (
        select(Customer)
        .options(selectinload(Customer.notes))
        .where(*filters)
        .order_by(Customer.last_contact.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    total = await session.scalar(select(func.count()).select_from(Customer).where(*filters))
    customers = list((await session.scalars(stmt)).all())

    return {
        "customers": [serialize_customer(c) for c in customers],
        "pagination": {"page": page, "limit": limit, "total": total, "totalPages": ...},
    }
```

### 3.2 GDPR 数据导出

**TypeScript (`src/app/api/customers/[id]/gdpr/export/route.ts`):**
```typescript
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const auth = await requireAuth(request, "customers:read");
  if (!isAuthenticated(auth)) return auth;

  const customer = await prisma.customer.findUnique({
    where: { id: params.id },
    include: {
      notes: true,
      conversations: { include: { messages: true } },
    },
  });

  if (!customer) {
    return NextResponse.json({ error: "Customer not found" }, { status: 404 });
  }

  return NextResponse.json({
    exportDate: new Date().toISOString(),
    format: "GDPR Data Export",
    customer: {
      id: customer.id,
      name: customer.name,
      email: customer.email,
      // ... 其他字段
    },
    notes: customer.notes,
    conversations: customer.conversations,
  });
}
```

**Python (`backend/app/domain/gdpr/service.py`):**
```python
async def export_customer_data(self, customer_id: str) -> dict[str, Any] | None:
    customer = await self.session.scalar(
        select(Customer)
        .options(
            selectinload(Customer.notes),
            selectinload(Customer.conversations).selectinload(Conversation.messages),
        )
        .where(Customer.id == customer_id)
    )

    if not customer:
        return None

    return {
        "exportDate": datetime.now(UTC).isoformat(),
        "format": "GDPR Data Export",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "whatsapp": customer.whatsapp,
            "tags": customer.tags,
            "firstContact": customer.first_contact.isoformat() if customer.first_contact else None,
            "lastContact": customer.last_contact.isoformat() if customer.last_contact else None,
            "createdAt": customer.created_at.isoformat() if customer.created_at else None,
        },
        "notes": [...],
        "conversations": [...],
    }
```

### 3.3 GDPR 数据删除

**TypeScript:**
```typescript
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // 简单删除
  await prisma.customer.delete({ where: { id: params.id } });
  return NextResponse.json({ success: true });
}
```

**Python (增强版):**
```python
async def delete_customer_data(
    self, customer_id: str, hard_delete: bool = False
) -> dict[str, Any]:
    customer = await self.session.scalar(
        select(Customer).options(selectinload(Customer.conversations))
        .where(Customer.id == customer_id)
    )

    if not customer:
        return {"success": False, "deletedRecords": 0}

    deleted_records = 0

    if hard_delete:
        # 完全删除所有关联数据
        for conv in customer.conversations:
            messages = await self.session.scalars(
                select(Message).where(Message.conversation_id == conv.id)
            )
            for msg in messages:
                await self.session.delete(msg)
                deleted_records += 1
            await self.session.delete(conv)
            deleted_records += 1
        await self.session.delete(customer)
        deleted_records += 1
    else:
        # 软删除：脱敏后保留记录
        for conv in customer.conversations:
            messages = await self.session.scalars(
                select(Message).where(Message.conversation_id == conv.id)
            )
            for msg in messages:
                msg.content = "[REDACTED - GDPR]"
                deleted_records += 1
        # ... 更新客户信息
        await self.session.delete(customer)
        deleted_records += 1

    await self.session.commit()
    return {"success": True, "deletedRecords": deleted_records}
```

## 4. 新增功能

### 4.1 PII 脱敏 (Python 独有)

```python
PII_PATTERNS = [
    ("credit_card", re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARD REDACTED]"),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN REDACTED]"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL REDACTED]"),
    ("phone", re.compile(r"\b\+?\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,9}\b"), "[PHONE REDACTED]"),
    ("ip_address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP REDACTED]"),
]

def redact_pii(text: str) -> str:
    redacted = text
    for _, pattern, replacement in PII_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted

def detect_pii(text: str) -> dict[str, Any]:
    types: list[str] = []
    for name, pattern, _ in PII_PATTERNS:
        if pattern.search(text):
            types.append(name)
    return {"found": len(types) > 0, "types": types}
```

### 4.2 数据保留策略 (Python 独有)

```python
async def apply_retention_policy(self, retention_days: int) -> dict[str, int]:
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)

    old_conversations = await self.session.scalars(
        select(Conversation).where(
            Conversation.status.in_(["resolved", "closed"]),
            Conversation.updated_at <= cutoff,
        )
    )

    messages_deleted = 0
    for conv in old_conversations:
        messages = await self.session.scalars(
            select(Message).where(Message.conversation_id == conv.id)
        )
        for msg in messages:
            await self.session.delete(msg)
            messages_deleted += 1

    conversations_deleted = len(old_conversations)
    for conv in old_conversations:
        await self.session.delete(conv)

    await self.session.commit()
    return {"conversationsDeleted": conversations_deleted, "messagesDeleted": messages_deleted}
```

## 5. API 端点对比

| 功能 | TypeScript | Python |
|------|------------|--------|
| 列表 | `GET /api/customers` | `GET /api/v1/customers` |
| 创建 | `POST /api/customers` | `POST /api/v1/customers` |
| 获取 | `GET /api/customers/[id]` | `GET /api/v1/customers/{id}` |
| 更新 | `PUT /api/customers/[id]` | `PUT /api/v1/customers/{id}` |
| 删除 | `DELETE /api/customers/[id]` | `DELETE /api/v1/customers/{id}` |
| 笔记列表 | `GET /[id]/notes` | `GET /{id}/notes` |
| 创建笔记 | `POST /[id]/notes` | `POST /{id}/notes` |
| 对话列表 | `GET /[id]/conversations` | `GET /{id}/conversations` |
| GDPR 导出 | `GET /[id]/gdpr/export` | `GET /{id}/gdpr/export` |
| GDPR 删除 | `DELETE /[id]/gdpr/delete` | `DELETE /{id}/gdpr/delete?hardDelete=true` |

## 6. 数据模型对比

**TypeScript (Prisma):**
```prisma
model Customer {
  id          String   @id @default(cuid())
  name        String
  email       String?
  phone       String?
  whatsapp    String?
  tags        String?
  isBlocked   Boolean  @default(false)
  metadata    Json?
  firstContact DateTime?
  lastContact  DateTime?
  notes       CustomerNote[]
  conversations Conversation[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    whatsapp: Mapped[str | None] = mapped_column(String(50))
    tags: Mapped[list | None] = mapped_column(JSON)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)
    first_contact: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    last_contact: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    notes: Mapped[list["CustomerNote"]] = relationship(back_populates="customer")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer")
```

## 7. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 基本功能 | ✅ 完整 | ✅ 完整 |
| GDPR 合规 | 基础 | 增强（软删除、硬删除） |
| PII 脱敏 | ❌ | ✅ |
| 数据保留策略 | ❌ | ✅ |
| 架构 | 单文件 | 分层架构 |

Python 版本在 GDPR 合规方面做了显著增强，提供了更完善的数据保护和隐私管理功能。
