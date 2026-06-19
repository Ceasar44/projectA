# 运营配置模块 Operations

## 业务流程

运营配置当前拆成多个 API 模块，但底层都属于客服运营能力：

1. 营业时间：配置一周内各天营业时间和离线提示。
2. SLA：配置不同渠道/优先级下的首次响应和解决时限。
3. 快捷回复：配置客服常用回复模板和快捷指令。
4. 会话处理、工单处理或前端页面读取这些配置，辅助客服日常工作。

## 领域对象与关系

- `BusinessHours`：营业时间配置。
- `SLARule`：SLA 规则。
- `CannedResponse`：快捷回复模板。
- `OperationsService`：旧聚合服务，提供营业时间、SLA、快捷回复的兼容操作。
- `BusinessHoursService`、`SLAService`、`CannedResponseService`：拆分后的专用服务。

关系说明：

- 三类对象当前没有数据库外键。
- SLA 规则通过 `channel`、`priority` 字符串匹配会话或工单。
- 快捷回复通过 `shortcut` 被前端或客服输入引用。

## 状态机

### 营业时间

```text
disabled
  └─ enabled=true -> enabled
enabled
  ├─ 当前时间在配置范围内 -> open
  ├─ 当前时间不在配置范围内 -> closed
  └─ enabled=false -> disabled
```

### SLA 规则

```text
inactive
  └─ is_active=true -> active
active
  ├─ 会话/工单满足条件 -> apply
  └─ is_active=false -> inactive
```

### 快捷回复

```text
inactive
  └─ is_active=true -> active
active
  ├─ 使用一次 -> active，usage_count + 1
  └─ is_active=false -> inactive
```

## 模块结构

- `backend/app/api/v1/business_hours.py`：营业时间 API。
- `backend/app/api/v1/sla.py`：SLA API。
- `backend/app/api/v1/canned_responses.py`：快捷回复 API。
- `backend/app/api/v1/operations.py`：旧聚合 API，当前未挂载主路由。
- `backend/app/domain/business_hours/service.py`：营业时间服务。
- `backend/app/domain/sla/service.py`：SLA 服务。
- `backend/app/domain/canned_responses/service.py`：快捷回复服务。
- `backend/app/domain/operations/service.py`：运营聚合服务。
- `backend/app/infrastructure/db/models/operations.py`：相关模型。
