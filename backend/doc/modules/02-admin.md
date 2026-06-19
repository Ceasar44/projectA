# 管理后台模块 Admin

## 业务流程

1. 管理员登录后访问 `/api/admin/users` 管理后台用户。
2. 创建用户时写入 `Admin` 表，密码由安全工具进行哈希。
3. 更新用户时可修改名称、角色、密码等字段。
4. 删除用户时从 `Admin` 表移除记录。
5. 管理员访问 `/api/admin/api-keys` 管理外部系统 API Key。
6. 插件列表接口返回当前后端支持的插件/扩展信息。

## 领域对象与关系

- `Admin`：后台用户。
- `ApiKey`：外部接口访问凭证。
- `AdminUserCreate`、`AdminUserUpdate`、`AdminUserRead`：后台用户 DTO。
- `ApiKeyCreate`、`ApiKeyUpdate`、`ApiKeyRead`：API Key DTO。

关系说明：

- 管理后台模块直接复用认证模块的 `Admin`、`ApiKey` 表。
- 当前没有“用户创建者”“API Key 所属用户”等外键关系。

## 状态机

### 管理员账号

```text
创建
  ├─ 更新资料/角色/密码 -> 可继续使用
  └─ 删除 -> 不可登录
```

### API Key

```text
启用
  ├─ 禁用 -> 停止认证
  ├─ 更新名称/状态 -> 启用或禁用
  └─ 删除 -> 不可使用
禁用
  └─ 启用 -> 可用于认证
```

## 模块结构

- `backend/app/api/v1/admin.py`：管理后台 API。
- `backend/app/domain/admin/service.py`：用户和 API Key 管理逻辑。
- `backend/app/domain/admin/schemas.py`：管理后台 schema。
- `backend/app/infrastructure/db/models/auth.py`：`Admin`、`ApiKey` 表。
- `backend/app/infrastructure/db/repositories/admin.py`：管理后台仓储。
- `backend/app/api/deps.py`：管理员权限校验。
