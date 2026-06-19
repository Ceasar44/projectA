# 客户模块 Customers

## 业务流程

1. 客服或系统创建客户，写入 `customer` 表。
2. 客户可通过邮箱、电话、WhatsApp 等联系方式被检索。
3. 客户发起会话时，会话可关联到 `customer_id`。
4. 客服可为客户添加备注，写入 `customer_note`。
5. 客户详情页聚合展示客户资料、备注和关联会话。
6. GDPR 接口可导出客户相关数据，或删除/匿名化客户数据。

## 领域对象与关系

- `Customer`：客户主对象。
- `CustomerNote`：客户备注。
- `Conversation`：客户关联的客服会话。
- `CustomerCreate`、`CustomerUpdate`、`CustomerDetail`：客户 DTO。
- `GDPRService`：负责客户数据导出、删除和匿名化。

关系说明：

- `customer.id` 1 对多 `customer_note.customer_id`，删除客户时备注级联删除。
- `customer.id` 1 对多 `conversation.customer_id`，删除客户时会话的客户字段置空。
- `customer.id` 也被 AI 工作台、自动客服日志等表引用。

## 状态机

### 客户封禁状态

```text
正常
  └─ 设置 is_blocked=true -> 已封禁
已封禁
  └─ 设置 is_blocked=false -> 正常
```

### GDPR 处理

```text
正常客户数据
  ├─ export -> 数据不变，返回导出包
  ├─ anonymize -> 客户身份信息被脱敏
  └─ delete -> 客户及可级联数据删除/业务引用置空
```

## 模块结构

- `backend/app/api/v1/customers.py`：客户 API。
- `backend/app/domain/customer/service.py`：客户 CRUD 和备注逻辑。
- `backend/app/domain/customer/schemas.py`：客户 schema。
- `backend/app/domain/gdpr/service.py`：GDPR 导出、删除、脱敏。
- `backend/app/infrastructure/db/models/conversations.py`：`Customer`、`CustomerNote`、`Conversation`。
- `backend/app/infrastructure/db/repositories/customers.py`：客户仓储。
