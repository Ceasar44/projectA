# Conversations 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中对话模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/
├── lib/
│   └── conversation-engine.ts    # 对话引擎核心逻辑
├── app/api/conversations/
│   ├── route.ts                  # 列表/创建
│   └── [id]/
│       ├── route.ts              # 获取/更新/删除
│       ├── messages/route.ts     # 消息管理
│       ├── notes/route.ts        # 内部笔记
│       ├── transfer/route.ts     # 转移
│       ├── merge/route.ts        # 合并
│       ├── snooze/route.ts       # 暂停
│       ├── route-to/route.ts     # 路由分配
│       ├── macro/route.ts        # 宏执行
│       └── satisfaction/route.ts # 满意度
```

### Python (backend) 架构

```
backend/app/
├── domain/conversation/
│   ├── schemas.py                # 数据模型
│   ├── service.py                # 业务逻辑
│   └── engine.py                 # 对话引擎
├── api/v1/
│   └── conversations.py          # 所有端点集中
├── infrastructure/db/
│   ├── models/conversations.py   # 数据库模型
│   └── repositories/conversations.py
└── infrastructure/realtime/
    └── __init__.py               # 实时事件推送
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 对话列表 | ✅ GET /api/conversations | ✅ GET /api/v1/conversations | ✅ 一致 |
| 创建对话 | ✅ POST /api/conversations | ✅ POST /api/v1/conversations | ✅ 一致 |
| 获取对话 | ✅ GET /api/conversations/[id] | ✅ GET /api/v1/conversations/{id} | ✅ 一致 |
| 更新对话 | ✅ PUT /api/conversations/[id] | ✅ PUT /api/v1/conversations/{id} | ✅ 一致 |
| 删除对话 | ✅ DELETE /api/conversations/[id] | ✅ DELETE /api/v1/conversations/{id} | ✅ 一致 |
| 消息列表 | ✅ GET /[id]/messages | ✅ GET /{id}/messages | ✅ 一致 |
| 发送消息 | ✅ POST /[id]/messages | ✅ POST /{id}/messages | ✅ 一致 |
| 转移对话 | ✅ POST /[id]/transfer | ✅ POST /{id}/transfer | ✅ 一致 |
| 合并对话 | ✅ POST /[id]/merge | ✅ POST /{id}/merge | ✅ 一致 |
| 暂停对话 | ✅ POST /[id]/snooze | ✅ POST /{id}/snooze | ✅ 一致 |
| 路由分配 | ✅ POST /[id]/route-to | ✅ POST /{id}/route-to | ✅ 一致 |
| 宏执行 | ✅ POST /[id]/macro | ✅ POST /{id}/macro | ✅ 一致 |
| 满意度评价 | ✅ POST /[id]/satisfaction | ✅ POST /{id}/satisfaction | ✅ 一致 |
| 内部笔记 | ✅ GET/POST /[id]/notes | ✅ GET/POST /{id}/notes | ✅ 一致 |
| 实时推送 | ✅ SSE | ✅ SSE | ✅ 一致 |

## 3. 核心代码对比

### 3.1 对话路由引擎

**TypeScript (`src/lib/conversation-engine.ts`):**
```typescript
export type RoutingStrategy = "round_robin" | "least_busy" | "skill_based" | "priority";

export async function routeConversation(
  conversationId: string,
  strategy: RoutingStrategy = "skill_based",
  requiredExpertise?: string,
  departmentId?: string
): Promise<RoutingResult | null> {
  const where: Record<string, unknown> = { isAvailable: true };
  if (departmentId) where.departmentId = departmentId;

  const members = await prisma.teamMember.findMany({
    where,
    include: { department: true, _count: { select: { tickets: true } } },
    orderBy: { createdAt: "asc" },
  });

  if (members.length === 0) return null;

  let selected;
  switch (strategy) {
    case "skill_based":
      if (requiredExpertise) {
        const expertiseLower = requiredExpertise.toLowerCase();
        selected = members.find((m) =>
          m.expertise.toLowerCase().includes(expertiseLower)
        );
      }
      if (!selected) selected = members[0];
      break;

    case "least_busy":
      selected = members.reduce((min, m) =>
        m._count.tickets < min._count.tickets ? m : min
      );
      break;

    case "round_robin":
      const lastTicket = await prisma.ticket.findFirst({
        where: { assignedToId: { not: null } },
        orderBy: { createdAt: "desc" },
        select: { assignedToId: true },
      });
      if (lastTicket?.assignedToId) {
        const lastIndex = members.findIndex((m) => m.id === lastTicket.assignedToId);
        selected = members[(lastIndex + 1) % members.length];
      } else {
        selected = members[0];
      }
      break;

    case "priority":
    default:
      selected = members[0];
      break;
  }

  return {
    assignedToId: selected.id,
    assignedToName: selected.name,
    departmentId: selected.departmentId,
    departmentName: selected.department.name,
    reason: `Routed via ${strategy} strategy`,
  };
}
```

**Python (`backend/app/domain/conversation/engine.py`):**
```python
from enum import Enum

class RoutingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    SKILL_BASED = "skill_based"
    PRIORITY = "priority"

@dataclass
class RoutingResult:
    assigned_to_id: str
    assigned_to_name: str
    department_id: str
    department_name: str
    reason: str

class ConversationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def route_conversation(
        self,
        conversation_id: str,
        strategy: RoutingStrategy = RoutingStrategy.SKILL_BASED,
        required_expertise: str | None = None,
        department_id: str | None = None,
    ) -> RoutingResult | None:
        filters = [TeamMember.is_available == True]
        if department_id:
            filters.append(TeamMember.department_id == department_id)

        members = list(
            (await self.session.scalars(
                select(TeamMember)
                .options(selectinload(TeamMember.department))
                .where(*filters)
                .order_by(TeamMember.created_at)
            )).all()
        )

        if not members:
            return None

        selected = None
        if strategy == RoutingStrategy.SKILL_BASED:
            if required_expertise:
                expertise_lower = required_expertise.lower()
                for m in members:
                    if expertise_lower in (m.expertise or "").lower():
                        selected = m
                        break
            if not selected:
                selected = members[0]

        elif strategy == RoutingStrategy.LEAST_BUSY:
            ticket_counts = {}
            for m in members:
                count = await self.session.scalar(
                    select(func.count()).where(Ticket.assigned_to_id == m.id)
                )
                ticket_counts[m.id] = count or 0
            selected = min(members, key=lambda m: ticket_counts[m.id])

        elif strategy == RoutingStrategy.ROUND_ROBIN:
            last_ticket = await self.session.scalar(
                select(Ticket)
                .where(Ticket.assigned_to_id.isnot(None))
                .order_by(Ticket.created_at.desc())
            )
            if last_ticket and last_ticket.assigned_to_id:
                last_index = next(
                    (i for i, m in enumerate(members) if m.id == last_ticket.assigned_to_id), -1
                )
                selected = members[(last_index + 1) % len(members)]
            else:
                selected = members[0]

        else:  # PRIORITY
            selected = members[0]

        return RoutingResult(
            assigned_to_id=selected.id,
            assigned_to_name=selected.name,
            department_id=selected.department_id,
            department_name=selected.department.name if selected.department else "",
            reason=f"Routed via {strategy.value} strategy",
        )
```

**差异分析:**
- 两者实现相同的四种路由策略
- Python 使用 Enum 定义策略类型，更安全
- Python 使用 dataclass 定义返回结果
- 两者逻辑完全一致

### 3.2 对话转移

**TypeScript:**
```typescript
export async function transferConversation(
  conversationId: string,
  toMemberId: string,
  fromMemberName: string,
  note?: string
): Promise<boolean> {
  const member = await prisma.teamMember.findUnique({
    where: { id: toMemberId },
    select: { id: true, name: true },
  });

  if (!member) return false;

  // 更新所有开放工单
  await prisma.ticket.updateMany({
    where: { conversationId, status: { in: ["open", "in_progress"] } },
    data: { assignedToId: toMemberId },
  });

  // 添加内部笔记
  await prisma.internalNote.create({
    data: {
      conversationId,
      content: `Conversation transferred from ${fromMemberName} to ${member.name}${note ? `: ${note}` : ""}`,
      authorName: "System",
    },
  });

  return true;
}
```

**Python:**
```python
async def transfer_conversation(
    self,
    conversation_id: str,
    to_member_id: str,
    from_member_name: str,
    note: str | None = None,
) -> bool:
    member = await self.session.scalar(
        select(TeamMember).where(TeamMember.id == to_member_id)
    )
    if not member:
        return False

    await self.session.execute(
        update(Ticket)
        .where(
            Ticket.conversation_id == conversation_id,
            Ticket.status.in_(["open", "in_progress"]),
        )
        .values(assigned_to_id=to_member_id)
    )

    internal_note = InternalNote(
        conversation_id=conversation_id,
        content=f"Conversation transferred from {from_member_name} to {member.name}"
        + (f": {note}" if note else ""),
        author_name="System",
    )
    self.session.add(internal_note)
    await self.session.commit()

    return True
```

### 3.3 宏执行

**TypeScript:**
```typescript
export async function executeMacro(
  conversationId: string,
  actions: { type: string; value: string }[],
  authorName: string
): Promise<{ executed: number; errors: string[] }> {
  let executed = 0;
  const errors: string[] = [];

  for (const action of actions) {
    try {
      switch (action.type) {
        case "set_status":
          await prisma.conversation.update({
            where: { id: conversationId },
            data: { status: action.value },
          });
          executed++;
          break;

        case "assign_department": {
          const dept = await prisma.department.findFirst({
            where: { name: { contains: action.value, mode: "insensitive" } },
          });
          if (dept) {
            await prisma.ticket.updateMany({
              where: { conversationId },
              data: { departmentId: dept.id },
            });
            executed++;
          }
          break;
        }

        case "add_tag": {
          let tag = await prisma.tag.findUnique({ where: { name: action.value } });
          if (!tag) {
            tag = await prisma.tag.create({ data: { name: action.value } });
          }
          await prisma.conversationTag.create({
            data: { conversationId, tagId: tag.id },
          }).catch(() => {});
          executed++;
          break;
        }

        case "add_note":
          await prisma.internalNote.create({
            data: { conversationId, content: action.value, authorName },
          });
          executed++;
          break;

        case "send_message":
          await prisma.message.create({
            data: { conversationId, role: "assistant", content: action.value },
          });
          executed++;
          break;
      }
    } catch (err) {
      errors.push(`${action.type}: ${err.message}`);
    }
  }

  return { executed, errors };
}
```

**Python:**
```python
async def execute_macro(
    self,
    conversation_id: str,
    actions: list[dict[str, str]],
    author_name: str,
) -> tuple[int, list[str]]:
    executed = 0
    errors: list[str] = []

    for action in actions:
        action_type = action.get("type", "")
        value = action.get("value", "")

        try:
            if action_type == "set_status":
                await self.session.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation_id)
                    .values(status=value)
                )
                executed += 1

            elif action_type == "assign_department":
                dept = await self.session.scalar(
                    select(Department).where(Department.name.ilike(f"%{value}%"))
                )
                if dept:
                    await self.session.execute(
                        update(Ticket)
                        .where(Ticket.conversation_id == conversation_id)
                        .values(department_id=dept.id)
                    )
                    executed += 1

            elif action_type == "add_tag":
                tag = await self.session.scalar(
                    select(Tag).where(Tag.name == value)
                )
                if not tag:
                    tag = Tag(name=value)
                    self.session.add(tag)
                    await self.session.flush()
                # ... 添加标签关联
                executed += 1

            elif action_type == "add_note":
                note = InternalNote(
                    conversation_id=conversation_id,
                    content=value,
                    author_name=author_name,
                )
                self.session.add(note)
                executed += 1

            elif action_type == "send_message":
                message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=value,
                )
                self.session.add(message)
                executed += 1

        except Exception as e:
            errors.append(f"{action_type}: {str(e)}")

    await self.session.commit()
    return executed, errors
```

## 4. API 端点对比

### 4.1 对话列表

| TypeScript | Python |
|------------|--------|
| `GET /api/conversations` | `GET /api/v1/conversations` |

**查询参数:**
| 参数 | TypeScript | Python | 说明 |
|------|------------|--------|------|
| page | ✅ | ✅ | 页码 |
| limit | ✅ | ✅ | 每页数量 |
| channel | ✅ | ✅ | 渠道筛选 |
| status | ✅ | ✅ | 状态筛选 |
| search | ✅ | ✅ | 搜索关键词 |

### 4.2 子端点

| 功能 | TypeScript 端点 | Python 端点 |
|------|-----------------|-------------|
| 消息列表 | `GET /[id]/messages` | `GET /{id}/messages` |
| 发送消息 | `POST /[id]/messages` | `POST /{id}/messages` |
| 转移 | `POST /[id]/transfer` | `POST /{id}/transfer` |
| 合并 | `POST /[id]/merge` | `POST /{id}/merge` |
| 暂停 | `POST /[id]/snooze` | `POST /{id}/snooze` |
| 路由 | `POST /[id]/route-to` | `POST /{id}/route-to` |
| 宏 | `POST /[id]/macro` | `POST /{id}/macro` |
| 满意度 | `POST /[id]/satisfaction` | `POST /{id}/satisfaction` |
| 笔记 | `GET/POST /[id]/notes` | `GET/POST /{id}/notes` |

## 5. 实时事件推送

### TypeScript (`src/lib/realtime.ts`):
```typescript
export function emitNewMessage(
  conversationId: string,
  message: { id: string; role: string; content: string }
): void {
  publish(`conversation:${conversationId}`, {
    type: "message:new",
    conversationId,
    data: message,
  });
  publish("global", {
    type: "message:new",
    conversationId,
    data: { conversationId, messageId: message.id, role: message.role },
  });
}
```

### Python (`backend/app/infrastructure/realtime/__init__.py`):
```python
@classmethod
def emit_new_message(
    cls,
    conversation_id: str,
    message: dict[str, Any],
) -> None:
    event = EventPayload(
        type=EventType.MESSAGE_NEW,
        conversation_id=conversation_id,
        data=message,
    )
    cls.publish(f"conversation:{conversation_id}", event)
    cls.publish(
        "global",
        EventPayload(
            type=EventType.MESSAGE_NEW,
            conversation_id=conversation_id,
            data={
                "conversationId": conversation_id,
                "messageId": message.get("id"),
                "role": message.get("role"),
            },
        ),
    )
```

## 6. 数据模型对比

### Conversation 模型

**TypeScript (Prisma):**
```prisma
model Conversation {
  id              String   @id @default(cuid())
  channel         String
  customerName    String
  customerContact String
  status          String   @default("active")
  summary         String?
  satisfaction    Int?
  customerId      String?
  customer        Customer?  @relation(fields: [customerId], references: [id])
  messages        Message[]
  tickets         Ticket[]
  notes           InternalNote[]
  tags            ConversationTag[]
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel: Mapped[str] = mapped_column(String(50))
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_contact: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="active")
    summary: Mapped[str | None] = mapped_column(Text)
    satisfaction: Mapped[int | None] = mapped_column(Integer)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customer.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="conversation")
```

## 7. 工作流程图

### 7.1 消息发送流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      消息发送流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                API                    Database          │
│    │                    │                        │              │
│    │ POST /messages     │                        │              │
│    │───────────────────>│                        │              │
│    │                    │  INSERT INTO message   │              │
│    │                    │───────────────────────>│              │
│    │                    │                        │              │
│    │                    │  emit_new_message()    │              │
│    │                    │────────────────────┐   │              │
│    │                    │                    │   │              │
│    │                    │<───────────────────┘   │              │
│    │                    │                        │              │
│    │  SSE Event         │                        │              │
│    │<───────────────────│                        │              │
│    │                    │                        │              │
│    │  Response          │                        │              │
│    │<───────────────────│                        │              │
│    │                    │                        │              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 对话路由流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      对话路由流程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 获取可用客服列表                                             │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ SELECT * FROM team_member WHERE is_available = true │    │
│     └─────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  2. 根据策略选择客服                                             │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ skill_based: 匹配专业技能                            │    │
│     │ least_busy: 选择工单最少的                           │    │
│     │ round_robin: 轮询分配                                │    │
│     │ priority: 选择第一个                                 │    │
│     └─────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  3. 更新工单分配                                                 │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ UPDATE ticket SET assigned_to_id = ?                │    │
│     └─────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  4. 返回路由结果                                                 │
│     { assignedToId, assignedToName, departmentId, reason }     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 8. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 文件组织 | 分散在多个 route.ts | 集中在 conversations.py |
| 路由引擎 | 独立文件 | ConversationEngine 类 |
| 实时推送 | realtime.ts | infrastructure/realtime |
| 数据验证 | 手动 | Pydantic 模型 |
| 错误处理 | try/catch | try/except + HTTPException |
| 事务管理 | Prisma 自动 | Unit of Work 模式 |

Python 版本将所有对话相关端点集中在一个文件中，同时保持清晰的分层架构，便于维护和测试。
