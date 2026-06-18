# Team 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中团队模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/app/api/team/
├── members/
│   ├── route.ts           # 成员列表/创建
│   └── [id]/route.ts      # 成员 CRUD
└── departments/
    ├── route.ts           # 部门列表/创建
    └── [id]/route.ts      # 部门 CRUD
```

### Python (backend) 架构

```
backend/app/
├── api/v1/
│   └── team.py            # 所有团队相关端点
├── infrastructure/db/
│   ├── models/team.py     # TeamMember, Department 模型
│   └── repositories/team.py
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 成员列表 | ✅ GET /api/team/members | ✅ GET /api/v1/team/members | ✅ 一致 |
| 创建成员 | ✅ POST /api/team/members | ✅ POST /api/v1/team/members | ✅ 一致 |
| 获取成员 | ✅ GET /api/team/members/[id] | ✅ GET /api/v1/team/members/{id} | ✅ 一致 |
| 更新成员 | ✅ PUT /api/team/members/[id] | ✅ PUT /api/v1/team/members/{id} | ✅ 一致 |
| 删除成员 | ✅ DELETE /api/team/members/[id] | ✅ DELETE /api/v1/team/members/{id} | ✅ 一致 |
| 部门列表 | ✅ GET /api/team/departments | ✅ GET /api/v1/team/departments | ✅ 一致 |
| 创建部门 | ✅ POST /api/team/departments | ✅ POST /api/v1/team/departments | ✅ 一致 |
| 部门 CRUD | ✅ | ✅ | ✅ 一致 |

## 3. 核心代码对比

### 3.1 成员列表

**TypeScript (`src/app/api/team/members/route.ts`):**
```typescript
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request, "team:read");
  if (!isAuthenticated(auth)) return auth;

  const { searchParams } = new URL(request.url);
  const { page, limit, skip, take } = parsePagination(searchParams);
  const departmentId = searchParams.get("departmentId");

  const where = departmentId ? { departmentId } : {};

  const [members, total] = await Promise.all([
    prisma.teamMember.findMany({
      where,
      orderBy: { name: "asc" },
      skip,
      take,
      include: {
        department: { select: { id: true, name: true } },
      },
    }),
    prisma.teamMember.count({ where }),
  ]);

  return NextResponse.json(paginatedResponse(members, total, page, limit));
}
```

**Python (`backend/app/api/v1/team.py`):**
```python
@router.get("/members")
async def list_members(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    department_id: str | None = Query(default=None, alias="departmentId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    filters = []
    if department_id:
        filters.append(TeamMember.department_id == department_id)

    stmt = (
        select(TeamMember)
        .options(selectinload(TeamMember.department))
        .where(*filters)
        .order_by(TeamMember.name)
        .offset((page - 1) * limit)
        .limit(limit)
    )

    total = await session.scalar(select(func.count()).select_from(TeamMember).where(*filters))
    members = list((await session.scalars(stmt)).all())

    return {
        "data": [serialize_member(m) for m in members],
        "pagination": {...},
    }
```

### 3.2 创建成员

**TypeScript:**
```typescript
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { name, email, phone, role, expertise, departmentId } = body;

  if (!name || !name.trim()) {
    return NextResponse.json({ error: "Member name is required" }, { status: 400 });
  }

  if (!email || !email.trim()) {
    return NextResponse.json({ error: "Member email is required" }, { status: 400 });
  }

  if (!departmentId) {
    return NextResponse.json({ error: "Department is required" }, { status: 400 });
  }

  const member = await prisma.teamMember.create({
    data: {
      name: name.trim(),
      email: email.trim(),
      phone: phone?.trim() || "",
      role: role?.trim() || "member",
      expertise: expertise?.trim() || "",
      departmentId,
    },
    include: { department: { select: { id: true, name: true } } },
  });

  return NextResponse.json(member, { status: 201 });
}
```

**Python:**
```python
class MemberCreate(BaseModel):
    name: str
    email: str
    phone: str = ""
    role: str = "member"
    expertise: str = ""
    department_id: str

@router.post("/members", status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: MemberCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    member = TeamMember(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        expertise=payload.expertise,
        department_id=payload.department_id,
    )
    session.add(member)
    await session.commit()
    await session.refresh(member, ["department"])
    return serialize_member(member)
```

## 4. 数据模型对比

### TeamMember 模型

**TypeScript (Prisma):**
```prisma
model TeamMember {
  id           String     @id @default(cuid())
  name         String
  email        String     @unique
  phone        String?
  role         String     @default("member")
  expertise    String?
  isAvailable  Boolean    @default(true)
  departmentId String
  department   Department @relation(fields: [departmentId], references: [id])
  tickets      Ticket[]
  createdAt    DateTime   @default(now())
  updatedAt    DateTime   @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class TeamMember(Base):
    __tablename__ = "team_member"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(50), default="member")
    expertise: Mapped[str | None] = mapped_column(String(500))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("department.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    department: Mapped["Department"] = relationship(back_populates="members")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="assigned_to")
```

### Department 模型

**TypeScript (Prisma):**
```prisma
model Department {
  id          String       @id @default(cuid())
  name        String       @unique
  description String?
  members     TeamMember[]
  tickets     Ticket[]
  createdAt   DateTime     @default(now())
  updatedAt   DateTime     @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Department(Base):
    __tablename__ = "department"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    members: Mapped[list["TeamMember"]] = relationship(back_populates="department")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="department")
```

## 5. API 端点汇总

### 成员端点

| 方法 | TypeScript | Python |
|------|------------|--------|
| GET | `/api/team/members` | `/api/v1/team/members` |
| POST | `/api/team/members` | `/api/v1/team/members` |
| GET | `/api/team/members/[id]` | `/api/v1/team/members/{id}` |
| PUT | `/api/team/members/[id]` | `/api/v1/team/members/{id}` |
| DELETE | `/api/team/members/[id]` | `/api/v1/team/members/{id}` |

### 部门端点

| 方法 | TypeScript | Python |
|------|------------|--------|
| GET | `/api/team/departments` | `/api/v1/team/departments` |
| POST | `/api/team/departments` | `/api/v1/team/departments` |
| GET | `/api/team/departments/[id]` | `/api/v1/team/departments/{id}` |
| PUT | `/api/team/departments/[id]` | `/api/v1/team/departments/{id}` |
| DELETE | `/api/team/departments/[id]` | `/api/v1/team/departments/{id}` |

## 6. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 文件组织 | 分散在多个文件 | 集中在 team.py |
| 数据验证 | 手动验证 | Pydantic 模型 |
| 关联加载 | Prisma include | SQLAlchemy selectinload |
| 错误处理 | NextResponse | HTTPException |

Python 版本功能与 TypeScript 版本完全一致，采用更清晰的分层架构。
