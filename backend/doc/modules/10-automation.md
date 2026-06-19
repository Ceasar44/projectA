# 自动化模块 Automation

## 业务流程

1. 管理员创建自动化规则，定义触发类型、条件、动作和优先级。
2. 会话或消息事件发生时，业务层调用 `evaluate_rules`。
3. 服务加载启用的规则，并按条件判断是否命中。
4. 命中规则后返回动作列表或执行相应动作。
5. 规则触发次数可累加，用于统计规则效果。

## 领域对象与关系

- `AutomationRule`：自动化规则。
- `conditions`：JSON 条件数组，描述字段、操作符和值。
- `actions`：JSON 动作数组，描述自动回复、打标签、分配等动作。
- `AutomationService`：规则 CRUD 和规则评估服务。

关系说明：

- `AutomationRule` 当前没有数据库外键。
- 条件和动作通过 JSON 引用字段名、标签名、部门/成员 ID 等业务值。
- 会话模块在创建消息后可调用自动化模块。

## 状态机

### 规则启用状态

```text
inactive
  └─ is_active=true -> active
active
  ├─ 命中事件 -> active，trigger_count + 1
  └─ is_active=false -> inactive
```

### 规则匹配流程

```text
收到事件
  ├─ 规则未启用 -> skip
  ├─ 条件不满足 -> not_matched
  └─ 条件满足 -> matched -> 输出 actions
```

## 模块结构

- `backend/app/api/v1/automation.py`：自动化 API。
- `backend/app/domain/automation/service.py`：规则管理和评估。
- `backend/app/domain/automation/schemas.py`：自动化 schema。
- `backend/app/infrastructure/db/models/operations.py`：`AutomationRule`。
- `backend/app/infrastructure/db/repositories/automation.py`：自动化仓储。
