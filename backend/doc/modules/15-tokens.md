# Token 模块 Tokens

## 业务流程

1. 系统读取或创建默认 Token 钱包 `token_wallet/default`。
2. AI 调用、自动回复、外联生成等场景调用 `record_consumption` 记录消耗。
3. 用户创建充值订单，写入 `token_recharge_order`。
4. 支付完成后调用完成接口，订单变为完成，钱包余额增加。
5. 每次充值或消耗都会写入 `token_ledger_entry`，形成审计流水。
6. 前端通过 overview 接口查看余额、累计消耗、累计充值和趋势。

## 领域对象与关系

- `TokenWallet`：Token 钱包聚合。
- `TokenRechargeOrder`：充值订单。
- `TokenLedgerEntry`：余额流水。
- `TokenService`：估算、消耗、充值、概览服务。

关系说明：

- 三张表当前没有数据库外键。
- `TokenLedgerEntry.reference_id` 可业务引用订单 ID、AI 日志 ID、草稿 ID 等。
- `created_by_user_id` 可业务引用管理员 ID，但不是外键。

## 状态机

### 充值订单

```text
pending
  ├─ 支付成功/complete -> completed
  ├─ 支付失败 -> failed
  └─ 取消 -> cancelled
completed
  └─ 不应重复完成
```

### 钱包余额变动

```text
balance=N
  ├─ recharge(+x) -> balance=N+x
  ├─ consume(-x) -> balance=N-x
  └─ adjust(+/-x) -> balance=N+/-x
```

## 模块结构

- `backend/app/api/v1/tokens.py`：Token API。
- `backend/app/domain/tokens/service.py`：钱包、订单、流水服务。
- `backend/app/infrastructure/db/models/operations.py`：Token 相关模型。
