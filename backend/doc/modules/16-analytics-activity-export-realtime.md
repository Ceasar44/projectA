# 分析、活动、导出与实时模块

## 业务流程

### Analytics / Stats

1. 前端请求统计或分析接口。
2. 后端从会话、消息、工单、客户等表聚合数据。
3. 返回总量、渠道分布、解决率、趋势、团队表现等报表数据。

### Activity

1. 业务动作发生后调用 `ActivityService.log_activity`。
2. 操作日志写入 `activity_log`。
3. 前端按分页、实体类型、时间范围查询活动日志。

### Export

1. 用户选择导出类型：会话、客户、工单、知识库。
2. 后端查询对应数据并序列化。
3. 根据 `format=json/csv` 返回下载流。

### Realtime

1. 前端通过 `GET /api/realtime` 建立 SSE 连接。
2. 后端订阅全局频道或指定会话频道。
3. 业务事件通过 `event_bus` 发布。
4. SSE 持续推送事件和心跳。

## 领域对象与关系

- `ActivityLog`：活动日志。
- `AnalyticsRepository`：统计聚合查询。
- `EventPayload`：实时事件载荷。
- `event_bus`：进程内事件总线。
- `Conversation`、`Message`、`Customer`、`Ticket`、`KnowledgeEntry`：统计和导出的主要数据源。

关系说明：

- `ActivityLog` 当前没有外键，`entity` 和 `entity_id` 通过业务约定引用其他表。
- 实时事件不入库，主要通过内存事件总线推送。
- 导出模块不维护独立表。

## 状态机

### SSE 连接

```text
connecting
  └─ 建立成功 -> connected
connected
  ├─ 收到事件 -> connected
  ├─ heartbeat -> connected
  └─ 客户端断开/异常 -> disconnected
```

### 活动日志

活动日志是追加型记录，没有更新状态机：

```text
business_action -> append activity_log
```

## 模块结构

- `backend/app/api/v1/analytics.py`：统计和分析 API。
- `backend/app/api/v1/stats.py`：统计概览 API。
- `backend/app/api/v1/activity.py`：活动日志 API。
- `backend/app/api/v1/export.py`：数据导出 API。
- `backend/app/api/v1/realtime.py`：SSE 实时 API。
- `backend/app/domain/activity/service.py`：活动日志服务。
- `backend/app/domain/activity/schemas.py`：活动日志 schema。
- `backend/app/infrastructure/query/analytics.py`：分析查询。
- `backend/app/infrastructure/realtime/__init__.py`：实时事件总线。
