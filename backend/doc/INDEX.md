# Backend 模块对比文档总览

本文档库提供了 `backend` (Python/FastAPI) 与 `src` (TypeScript/Next.js) 代码实现的详细对比分析。

## 文档目录

| 文档 | 模块 | 说明 |
|------|------|------|
| [01-auth-module.md](./01-auth-module.md) | Auth | 认证模块对比 |
| [02-conversations-module.md](./02-conversations-module.md) | Conversations | 对话模块对比 |
| [03-customers-module.md](./03-customers-module.md) | Customers | 客户模块对比 |
| [04-team-module.md](./04-team-module.md) | Team | 团队模块对比 |
| [05-knowledge-module.md](./05-knowledge-module.md) | Knowledge | 知识库模块对比 |
| [06-webhooks-module.md](./06-webhooks-module.md) | Webhooks | Webhook 模块对比 |
| [07-settings-module.md](./07-settings-module.md) | Settings | 设置模块对比 |
| [08-channels-module.md](./08-channels-module.md) | Channels | 渠道模块对比 |
| [09-automation-module.md](./09-automation-module.md) | Automation | 自动化模块对比 |

## 架构对比

### TypeScript (src) 架构

```
src/
├── app/
│   ├── (auth)/              # 认证相关页面
│   ├── (dashboard)/         # 仪表盘页面
│   └── api/                 # API 路由 (Next.js App Router)
├── components/              # React 组件
└── lib/                     # 核心库
    ├── ai/                  # AI 引擎
    ├── channels/            # 渠道处理
    ├── hooks/               # React Hooks
    └── i18n/                # 国际化
```

**特点:**
- 使用 Next.js App Router
- API 路由与页面同目录结构
- Prisma ORM
- 直接数据库访问

### Python (backend) 架构

```
backend/app/
├── api/
│   ├── v1/                  # API 端点
│   └── router.py            # 路由注册
├── domain/                  # 领域层
│   ├── auth/
│   ├── conversation/
│   ├── customer/
│   └── ...
├── infrastructure/          # 基础设施层
│   ├── db/                  # 数据库
│   ├── realtime/            # 实时通信
│   ├── webhooks/            # Webhook 处理
│   └── channels/            # 渠道处理
└── core/                    # 核心配置
```

**特点:**
- 分层架构 (API/Domain/Infrastructure)
- Repository 模式
- Unit of Work 模式
- SQLAlchemy ORM
- 依赖注入

## 功能对比总表

| 模块 | TypeScript | Python | 差异说明 |
|------|------------|--------|----------|
| **Auth** | ✅ 完整 | ✅ 完整 | Python 新增 API Key 认证 |
| **Conversations** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Customers** | ✅ 完整 | ✅ 增强 | Python 新增 PII 脱敏、数据保留策略 |
| **Team** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Knowledge** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Webhooks** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Settings** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Channels** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Automation** | ✅ 完整 | ✅ 完整 | 功能完全一致 |
| **Realtime** | ✅ SSE | ✅ SSE | 功能完全一致 |
| **GDPR** | 基础 | ✅ 增强 | Python 新增完整 GDPR 合规 |
| **Activity** | ✅ | ✅ | 功能完全一致 |
| **Stats** | ✅ | ✅ | 功能完全一致 |
| **Export** | ✅ | ✅ | 功能完全一致 |

## 技术栈对比

| 方面 | TypeScript | Python |
|------|------------|--------|
| 框架 | Next.js 14 | FastAPI |
| ORM | Prisma | SQLAlchemy |
| 数据验证 | Zod / 手动 | Pydantic |
| 认证 | JWT + Cookie | JWT + Cookie + API Key |
| 实时通信 | SSE | SSE |
| HTTP 客户端 | fetch | httpx |
| 密码哈希 | bcryptjs | passlib |
| 任务调度 | setTimeout | 需外部调度器 |

## 新增功能 (Python 版本)

### 1. API Key 认证
```python
# 支持 X-API-Key header 认证
@router.get("/protected")
async def protected(auth: AuthContext = Depends(get_auth_context)):
    ...
```

### 2. PII 脱敏
```python
from app.domain.gdpr import redact_pii, detect_pii

# 自动识别并脱敏敏感信息
redacted = redact_pii("My card is 4111-1111-1111-1111")
# 输出: "My card is [CARD REDACTED]"
```

### 3. 数据保留策略
```python
# 自动清理过期数据
result = await gdpr_service.apply_retention_policy(retention_days=90)
# {"conversationsDeleted": 15, "messagesDeleted": 234}
```

### 4. 完整 GDPR 合规
- 数据导出 (`/customers/{id}/gdpr/export`)
- 数据删除 (`/customers/{id}/gdpr/delete?hardDelete=true`)
- 软删除与硬删除支持

## 迁移指南

### API 端点映射

| TypeScript | Python |
|------------|--------|
| `/api/auth` | `/api/v1/auth` |
| `/api/conversations` | `/api/v1/conversations` |
| `/api/customers` | `/api/v1/customers` |
| `/api/team/members` | `/api/v1/team/members` |
| `/api/knowledge/entries` | `/api/v1/knowledge/entries` |
| `/api/webhooks` | `/api/v1/webhooks` |
| `/api/settings` | `/api/v1/settings` |
| `/api/channels` | `/api/v1/channels` |
| `/api/automation` | `/api/v1/automation` |

### 命名约定差异

| TypeScript | Python |
|------------|--------|
| camelCase | snake_case |
| `customerName` | `customer_name` |
| `isBlocked` | `is_blocked` |
| `createdAt` | `created_at` |

### 响应格式

两者响应格式基本一致，Python 版本使用 Pydantic 模型确保类型安全。

## 总结

Python 版本在保持与 TypeScript 版本功能一致的基础上：

1. **架构更清晰**: 采用分层架构，便于测试和维护
2. **类型更安全**: Pydantic 模型提供运行时验证
3. **功能更完善**: 新增 GDPR 合规、PII 脱敏等功能
4. **扩展更方便**: Repository 模式便于切换数据源

所有核心业务逻辑与 TypeScript 版本保持一致，可无缝迁移。
