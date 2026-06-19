# 营销活动与流程模块 Campaigns / Flows

## 业务流程

### Campaigns

1. 管理员创建营销活动，配置渠道、主题、消息内容和客户分群。
2. 活动以 `draft` 状态保存。
3. 管理员可更新活动内容或计划时间。
4. 执行活动时，系统根据分群计算目标客户，并更新发送统计。
5. 活动完成后保留执行状态和发送数量。

### Flows

1. 管理员创建流程，配置节点列表和起始节点。
2. 流程保存为草稿或启用状态。
3. 发布前调用校验接口检查节点结构、起始节点等。
4. 业务事件触发时，启用流程可被执行，触发次数累加。

## 领域对象与关系

- `Campaign`：营销活动。
- `Flow`：流程定义。
- `segments`：活动目标分群 JSON。
- `nodes`：流程节点图 JSON。
- `CampaignService`：活动 CRUD 和执行。
- `FlowService`：流程 CRUD 和结构校验。

关系说明：

- `Campaign` 当前没有数据库外键，目标客户通过 `segments` 动态计算。
- `Flow` 当前没有数据库外键，节点内容保存在 JSON 中。

## 状态机

### Campaign

```text
draft
  ├─ schedule -> scheduled
  ├─ execute -> running
  └─ delete -> deleted
scheduled
  ├─ 到达计划时间 -> running
  └─ cancel -> draft/cancelled
running
  ├─ 执行成功 -> sent/completed
  └─ 执行失败 -> failed
```

### Flow

```text
inactive
  ├─ validate 通过并启用 -> active
  └─ validate 失败 -> invalid
active
  ├─ 事件触发 -> active，trigger_count + 1
  └─ 禁用 -> inactive
invalid
  └─ 修正节点并通过校验 -> inactive/active
```

## 模块结构

- `backend/app/api/v1/campaigns.py`：营销活动 API。
- `backend/app/api/v1/flows.py`：流程 API。
- `backend/app/domain/campaigns/service.py`：活动服务。
- `backend/app/domain/campaigns/schemas.py`：活动 schema。
- `backend/app/domain/flows/service.py`：流程服务。
- `backend/app/domain/flows/schemas.py`：流程 schema。
- `backend/app/infrastructure/db/models/operations.py`：`Campaign`、`Flow`。
- `backend/app/infrastructure/db/repositories/campaigns.py`：活动仓储。
- `backend/app/infrastructure/db/repositories/flows.py`：流程仓储。
