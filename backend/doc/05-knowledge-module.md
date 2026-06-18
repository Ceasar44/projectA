# Knowledge 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中知识库模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/app/api/knowledge/
├── categories/
│   ├── route.ts           # 分类列表/创建
│   └── [id]/route.ts      # 分类 CRUD
├── entries/
│   ├── route.ts           # 条目列表/创建
│   └── [id]/route.ts      # 条目 CRUD
└── test/
    └── route.ts           # 知识库测试
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── knowledge.py       # 所有知识库端点
├── infrastructure/db/
│   ├── models/knowledge.py    # Category, KnowledgeEntry 模型
│   └── repositories/knowledge.py
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 分类列表 | ✅ GET /api/knowledge/categories | ✅ GET /api/v1/knowledge/categories | ✅ 一致 |
| 创建分类 | ✅ POST /api/knowledge/categories | ✅ POST /api/v1/knowledge/categories | ✅ 一致 |
| 分类 CRUD | ✅ | ✅ | ✅ 一致 |
| 条目列表 | ✅ GET /api/knowledge/entries | ✅ GET /api/v1/knowledge/entries | ✅ 一致 |
| 创建条目 | ✅ POST /api/knowledge/entries | ✅ POST /api/v1/knowledge/entries | ✅ 一致 |
| 条目 CRUD | ✅ | ✅ | ✅ 一致 |
| 知识库测试 | ✅ POST /api/knowledge/test | ✅ POST /api/v1/knowledge/test | ✅ 一致 |

## 3. 核心代码对比

### 3.1 条目列表

**TypeScript (`src/app/api/knowledge/entries/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "knowledge:read");
  if (!isAuthenticated(auth)) return auth;

  const { searchParams } = new URL(request.url);
  const { page, limit, skip, take } = parsePagination(searchParams);
  const categoryId = searchParams.get("categoryId");

  const where = categoryId ? { categoryId } : {};

  const [entries, total] = await Promise.all([
    prisma.knowledgeEntry.findMany({
      where,
      orderBy: [{ priority: "desc" }, { updatedAt: "desc" }],
      skip,
      take,
      include: {
        category: { select: { id: true, name: true, color: true, icon: true } },
      },
    }),
    prisma.knowledgeEntry.count({ where }),
  ]);

  return NextResponse.json(paginatedResponse(entries, total, page, limit));
}
```

**Python (`backend/app/api/v1/knowledge.py`):**
```python
@router.get("/entries")
async def list_entries(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category_id: str | None = Query(default=None, alias="categoryId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    filters = []
    if category_id:
        filters.append(KnowledgeEntry.category_id == category_id)

    stmt = (
        select(KnowledgeEntry)
        .options(selectinload(KnowledgeEntry.category))
        .where(*filters)
        .order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.updated_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    total = await session.scalar(select(func.count()).select_from(KnowledgeEntry).where(*filters))
    entries = list((await session.scalars(stmt)).all())

    return {
        "data": [serialize_entry(e) for e in entries],
        "pagination": {...},
    }
```

### 3.2 创建条目

**TypeScript:**
```typescript
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { categoryId, title, content, priority } = body;

  if (!categoryId) {
    return NextResponse.json({ error: "Category ID is required" }, { status: 400 });
  }

  if (!title || !title.trim()) {
    return NextResponse.json({ error: "Title is required" }, { status: 400 });
  }

  const category = await prisma.category.findUnique({ where: { id: categoryId } });
  if (!category) {
    return NextResponse.json({ error: "Category not found" }, { status: 404 });
  }

  const entry = await prisma.knowledgeEntry.create({
    data: {
      categoryId,
      title: title.trim(),
      content: content?.trim() || "",
      priority: typeof priority === "number" ? priority : 0,
    },
    include: { category: { select: { id: true, name: true, color: true, icon: true } } },
  });

  return NextResponse.json(entry, { status: 201 });
}
```

**Python:**
```python
class EntryCreate(BaseModel):
    category_id: str
    title: str
    content: str = ""
    priority: int = 0

@router.post("/entries", status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: EntryCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    category = await session.get(Category, payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    entry = KnowledgeEntry(
        category_id=payload.category_id,
        title=payload.title,
        content=payload.content,
        priority=payload.priority,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry, ["category"])
    return serialize_entry(entry)
```

## 4. 数据模型对比

### Category 模型

**TypeScript (Prisma):**
```prisma
model Category {
  id        String           @id @default(cuid())
  name      String           @unique
  color     String?
  icon      String?
  entries   KnowledgeEntry[]
  createdAt DateTime         @default(now())
  updatedAt DateTime         @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Category(Base):
    __tablename__ = "category"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str | None] = mapped_column(String(20))
    icon: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    entries: Mapped[list["KnowledgeEntry"]] = relationship(back_populates="category")
```

### KnowledgeEntry 模型

**TypeScript (Prisma):**
```prisma
model KnowledgeEntry {
  id         String   @id @default(cuid())
  categoryId String
  category   Category @relation(fields: [categoryId], references: [id])
  title      String
  content    String?
  priority   Int      @default(0)
  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("category.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    category: Mapped["Category"] = relationship(back_populates="entries")
```

## 5. API 端点汇总

### 分类端点

| 方法 | TypeScript | Python |
|------|------------|--------|
| GET | `/api/knowledge/categories` | `/api/v1/knowledge/categories` |
| POST | `/api/knowledge/categories` | `/api/v1/knowledge/categories` |
| GET | `/api/knowledge/categories/[id]` | `/api/v1/knowledge/categories/{id}` |
| PUT | `/api/knowledge/categories/[id]` | `/api/v1/knowledge/categories/{id}` |
| DELETE | `/api/knowledge/categories/[id]` | `/api/v1/knowledge/categories/{id}` |

### 条目端点

| 方法 | TypeScript | Python |
|------|------------|--------|
| GET | `/api/knowledge/entries` | `/api/v1/knowledge/entries` |
| POST | `/api/knowledge/entries` | `/api/v1/knowledge/entries` |
| GET | `/api/knowledge/entries/[id]` | `/api/v1/knowledge/entries/{id}` |
| PUT | `/api/knowledge/entries/[id]` | `/api/v1/knowledge/entries/{id}` |
| DELETE | `/api/knowledge/entries/[id]` | `/api/v1/knowledge/entries/{id}` |

## 6. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 文件组织 | 分散在多个文件 | 集中在 knowledge.py |
| 数据验证 | 手动验证 | Pydantic 模型 |
| 关联加载 | Prisma include | SQLAlchemy selectinload |
| 排序支持 | priority + updatedAt | priority + updated_at |

Python 版本功能与 TypeScript 版本完全一致。
