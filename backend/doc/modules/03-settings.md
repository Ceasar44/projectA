# 系统设置模块 Settings

## 业务流程

1. 前端进入设置页后调用 `GET /api/settings` 获取全局配置。
2. 如果数据库中没有默认配置，仓储/服务层会创建或返回默认配置。
3. 管理员修改业务信息、AI 参数、邮件、电话、WhatsApp、Telegram 等配置。
4. 前端调用 `PUT /api/settings` 保存，后端更新 `settings` 表。
5. 其他模块读取设置，例如 AI 回复、渠道连接、外联发送和电话回调。

## 领域对象与关系

- `Settings`：全局设置聚合根，数据库通常只有 `id=default` 一条主记录。
- `SettingsRead`：设置读取响应。
- `SettingsUpdate`：设置更新请求。

关系说明：

- `Settings` 当前没有外键。
- AI 工作台、客服 Agent、渠道模块会读取 `Settings`，但只是业务依赖，不是数据库关系。

## 状态机

配置本身没有复杂状态机，主要是单例配置的生命周期：

```text
不存在
  └─ 首次读取/写入 -> 默认配置
默认配置
  └─ 管理员更新 -> 自定义配置
自定义配置
  └─ 管理员再次更新 -> 自定义配置
```

## 模块结构

- `backend/app/api/v1/settings.py`：设置 API。
- `backend/app/domain/settings/service.py`：设置读取和更新逻辑。
- `backend/app/domain/settings/schemas.py`：设置 schema。
- `backend/app/infrastructure/db/models/operations.py`：`Settings` 数据模型。
- `backend/app/infrastructure/db/repositories/settings.py`：设置仓储。
