# Automation 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中自动化模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/app/api/automation/
├── route.ts              # 规则列表/创建
└── [id]/route.ts         # 规则 CRUD
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── automation.py     # 自动化 API 端点
└── infrastructure/db/
    └── models/operations.py  # AutomationRule 模型
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 规则列表 | ✅ GET /api/automation | ✅ GET /api/v1/automation | ✅ 一致 |
| 创建规则 | ✅ POST /api/automation | ✅ POST /api/v1/automation | ✅ 一致 |
| 规则 CRUD | ✅ | ✅ | ✅ 一致 |
| 规则触发 | ✅ | ✅ | ✅ 一致 |
| 优先级排序 | ✅ | ✅ | ✅ 一致 |

## 3. 核心代码对比

### 3.1 规则列表

**TypeScript (`src/app/api/automation/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "automation:read");
  if (!isAuthenticated(auth)) return auth;

  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type");

  const where = type ? { type } : {};

  const rules = await prisma.automationRule.findMany({
    where,
    orderBy: [{ priority: "desc" }, { createdAt: "desc" }],
  });

  return NextResponse.json({ rules });
}
```

**Python (`backend/app/api/v1/automation.py`):**
```python
@router.get("")
async def list_rules(
    type: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    filters = []
    if type:
        filters.append(AutomationRule.type == type)

    rules = list(
        (await session.scalars(
            select(AutomationRule)
            .where(*filters)
            .order_by(AutomationRule.priority.desc(), AutomationRule.created_at.desc())
        )).all()
    )
    return {"rules": [serialize_rule(r) for r in rules]}
```

### 3.2 创建规则

**TypeScript:**
```typescript
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { name, description, type, conditions, actions, priority } = body;

  if (!name || !type) {
    return NextResponse.json({ error: "Name and type are required" }, { status: 400 });
  }

  const rule = await prisma.automationRule.create({
    data: {
      name,
      description: description || "",
      type,
      conditions: conditions || [],
      actions: actions || [],
      priority: priority || 0,
    },
  });

  return NextResponse.json(rule, { status: 201 });
}
```

**Python:**
```python
class RuleCreate(BaseModel):
    name: str
    description: str = ""
    type: str
    conditions: list = []
    actions: list = []
    priority: int = 0
    is_active: bool = True

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    rule = AutomationRule(
        name=payload.name,
        description=payload.description,
        type=payload.type,
        conditions=payload.conditions,
        actions=payload.actions,
        priority=payload.priority,
        is_active=payload.is_active,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return serialize_rule(rule)
```

## 4. 数据模型对比

**TypeScript (Prisma):**
```prisma
model AutomationRule {
  id           String   @id @default(cuid())
  name         String
  description  String?
  type         String
  isActive     Boolean  @default(true)
  conditions   Json?
  actions      Json?
  priority     Int      @default(0)
  triggerCount Int      @default(0)
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class AutomationRule(Base):
    __tablename__ = "automation_rule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000))
    type: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    conditions: Mapped[list | None] = mapped_column(JSON)
    actions: Mapped[list | None] = mapped_column(JSON)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

## 5. 规则类型

| 类型 | 说明 | TypeScript | Python |
|------|------|------------|--------|
| message_received | 消息接收触发 | ✅ | ✅ |
| conversation_created | 对话创建触发 | ✅ | ✅ |
| ticket_created | 工单创建触发 | ✅ | ✅ |
| schedule | 定时触发 | ✅ | ✅ |
| webhook | Webhook 触发 | ✅ | ✅ |

## 6. 条件与动作

### 条件示例

```json
{
  "conditions": [
    { "field": "channel", "operator": "equals", "value": "whatsapp" },
    { "field": "message.content", "operator": "contains", "value": "help" }
  ]
}
```

### 动作示例

```json
{
  "actions": [
    { "type": "send_message", "content": "How can I help you?" },
    { "type": "assign_department", "department": "Support" },
    { "type": "add_tag", "tag": "priority" }
  ]
}
```

## 7. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 规则存储 | JSON 字段 | JSON 字段 |
| 优先级 | priority 字段 | priority 字段 |
| 触发计数 | triggerCount | trigger_count |
| 数据验证 | 手动 | Pydantic 模型 |

Python 版本功能与 TypeScript 版本完全一致。
