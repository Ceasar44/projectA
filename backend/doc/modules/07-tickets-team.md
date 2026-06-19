# 工单与团队模块 Tickets / Team

## 业务流程

1. 管理员创建部门和团队成员。
2. 会话中出现需要跟进的问题时，客服或 Agent 创建工单。
3. 工单可关联会话、负责部门和指派成员。
4. 工单列表按状态、优先级等条件筛选。
5. 客服处理工单后更新状态、优先级、描述或解决方案。
6. 删除部门或成员时，工单上的部门/指派人字段置空，避免工单丢失。

## 领域对象与关系

- `Department`：部门。
- `TeamMember`：团队成员。
- `Ticket`：工单。
- `Schedule`：排班。
- `TicketService`：工单业务服务。

关系说明：

- `department.id` 1 对多 `team_member.department_id`。
- `department.id` 1 对多 `ticket.department_id`。
- `team_member.id` 1 对多 `ticket.assigned_to_id`。
- `conversation.id` 1 对多 `ticket.conversation_id`。
- `schedule.team_member_id` 与团队成员存在业务关系，但当前未声明数据库外键。

## 状态机

### 工单状态

```text
open
  ├─ 开始处理 -> in_progress
  ├─ 直接解决 -> resolved
  └─ 关闭 -> closed
in_progress
  ├─ 解决 -> resolved
  ├─ 暂停/等待 -> pending
  └─ 关闭 -> closed
pending
  └─ 恢复处理 -> in_progress
resolved
  ├─ 重新打开 -> open
  └─ 关闭 -> closed
closed
  └─ 重新打开 -> open
```

### 成员可用状态

```text
available=true
  └─ 标记不可用 -> available=false
available=false
  └─ 标记可用 -> available=true
```

## 模块结构

- `backend/app/api/v1/tickets.py`：工单 API。
- `backend/app/api/v1/team.py`：团队 API。
- `backend/app/domain/ticket/service.py`：工单服务。
- `backend/app/domain/ticket/schemas.py`：工单 schema。
- `backend/app/infrastructure/db/models/team.py`：部门、成员、工单、排班模型。
- `backend/app/infrastructure/db/repositories/tickets.py`：工单仓储。
