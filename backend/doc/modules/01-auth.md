# 认证模块 Auth

## 业务流程

1. 前端调用 `GET /api/auth` 判断系统是否已初始化，以及当前 Cookie/API Key 是否有效。
2. 首次部署时调用 `POST /api/auth/setup` 创建第一个管理员账号。
3. 管理员调用 `POST /api/auth/login` 登录，后端校验密码后签发认证 Cookie。
4. 已登录请求通过 `get_auth_context` 解析用户身份；管理接口还会通过 `require_role` 做角色校验。
5. 调用 `POST /api/auth/logout` 清理认证 Cookie。
6. 外部系统可用 API Key 认证，后端通过 `ApiKey` 表校验启用状态并更新最近使用时间。

## 领域对象与关系

- `Admin`：管理员账号，包含 `username`、`password`、`name`、`role`。
- `ApiKey`：外部访问凭证，包含 `name`、`key`、`is_active`、`last_used`。
- `AuthContext`：请求级身份上下文，不直接入库，统一描述当前用户或 API Key。
- `SetupRequest`、`LoginRequest`、`AuthStatusResponse`：认证接口请求/响应对象。

关系说明：

- `Admin` 与 `ApiKey` 当前没有数据库外键关系。
- `AuthContext.user_id` 在业务上可对应 `Admin.id`。
- API Key 认证成功后也会生成 `AuthContext`，用于后续权限判断。

## 状态机

### 系统初始化状态

```text
未初始化
  └─ setup 成功 -> 已初始化
已初始化
  └─ setup 再次调用 -> 拒绝
```

### 登录状态

```text
未登录
  └─ login 成功 -> 已登录
已登录
  ├─ logout -> 未登录
  └─ Cookie 过期/无效 -> 未登录
```

### API Key 状态

```text
active=true
  └─ 管理员禁用 -> active=false
active=false
  └─ 管理员启用 -> active=true
```

## 模块结构

- `backend/app/api/v1/auth.py`：认证 API 入口。
- `backend/app/domain/auth/service.py`：认证业务逻辑。
- `backend/app/domain/auth/schemas.py`：认证请求/响应 schema。
- `backend/app/infrastructure/db/models/auth.py`：`Admin`、`ApiKey` 数据模型。
- `backend/app/infrastructure/db/repositories/auth.py`：管理员和 API Key 仓储。
- `backend/app/api/deps.py`：请求身份解析与权限依赖。
- `backend/app/core/security.py`：密码哈希、token/Cookie 等安全工具。
