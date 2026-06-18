# Owly 前后端维护指南

## 1. 文档目的

这份文档面向后续接手当前 Owly 代码库的维护者。

它的目标是详细说明：

- 当前 `frontend` 与 `backend` 是如何协同工作的
- 请求如何从浏览器流转到 Next.js，再流转到 FastAPI
- 当前认证机制是如何实现的
- 关键代码分别位于哪些目录和文件
- 哪些部分相对稳定，哪些部分修改时需要格外小心
- 如何在不破坏现有功能的前提下修改页面、接口契约和后端逻辑

这份文档会尽量写得详细，因为当前项目已经不是原来那个单体 TypeScript 应用，而是演进成了一个“拆分后的双项目结构”：

- `frontend/`：独立的 Next.js 前端项目
- `backend/`：独立的 FastAPI 后端项目

两者通过 API 契约、认证 cookie 和前端同源代理层强耦合在一起。

---

## 2. 当前系统的整体架构

### 2.1 当前拆分方式

- `frontend/`
  - 独立的 Next.js 16 应用
  - 负责页面渲染和所有 UI
  - 暴露本地 `/api/*` 代理路由，把请求转发给 FastAPI
  - 负责页面层面的登录/初始化跳转控制

- `backend/`
  - 独立的 FastAPI 应用
  - 负责认证、数据库、业务逻辑和真实 API 数据
  - 提供所有页面实际依赖的数据接口

### 2.2 请求流转方式

当前浏览器中的请求流如下：

1. 浏览器访问 `frontend`
2. 页面中的前端代码调用相对路径，例如 `/api/conversations`
3. Next.js 在 `frontend/src/app/api/[...path]/route.ts` 中接住这些请求
4. 该代理路由把请求转发给 `backend`，通常是 `http://127.0.0.1:8000/api/...`
5. FastAPI 处理请求并返回 JSON
6. Next.js 代理层把响应头、响应体、`set-cookie` 原样向浏览器返回
7. 浏览器把 `owly-token` cookie 存在前端域名下

这个“同源代理”设计非常重要。它解决了前期迁移过程中，前端直接跨域访问后端带来的 cookie 和登录态问题。

---

## 3. 仓库目录结构说明

### 3.1 顶层最重要的目录

- `frontend/`
  - 当前实际使用的独立前端项目
- `backend/`
  - 当前实际使用的独立后端项目
- `src/`
  - 原始 TypeScript 项目源码，目前主要作为迁移参考
- `prisma/`
  - 原项目 Prisma schema，是数据库结构的历史参考来源

### 3.2 Frontend 结构

前端最重要的文件：

- `frontend/package.json`
  - 前端依赖与脚本入口
- `frontend/next.config.ts`
  - Next.js 项目配置
- `frontend/.env.example`
  - 前端环境变量示例
- `frontend/src/app/layout.tsx`
  - 根布局
- `frontend/src/proxy.ts`
  - 页面级路由守卫
- `frontend/src/app/api/[...path]/route.ts`
  - 同源 API 代理层
- `frontend/src/components/layout/header.tsx`
  - 仪表盘页面的通用头部
- `frontend/src/components/providers.tsx`
  - 全局 React Provider
- `frontend/src/lib/hooks/use-theme.ts`
  - 主题切换和持久化状态

主要页面分组：

- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/setup/page.tsx`
- `frontend/src/app/(dashboard)/*`

### 3.3 Backend 结构

后端最重要的文件：

- `backend/pyproject.toml`
  - 后端依赖、pytest 配置
- `backend/.env.example`
  - 后端环境变量示例
- `backend/app/main.py`
  - FastAPI 应用创建入口
- `backend/app/api/router.py`
  - 总路由挂载入口
- `backend/app/core/config.py`
  - 环境配置加载
- `backend/app/core/database.py`
  - SQLAlchemy 引擎和 session 管理
- `backend/app/core/exceptions.py`
  - 全局异常处理与错误格式转换
- `backend/app/api/v1/*`
  - 所有 API 路由模块
- `backend/app/domain/*`
  - 业务层 service 和 schema
- `backend/app/infrastructure/db/*`
  - SQLAlchemy 模型与 repository
- `backend/tests/*`
  - 当前后端测试

---

## 4. 如何在本地启动系统

### 4.1 启动 Backend

推荐启动方式：

```powershell
cd D:\test\project2\owly\backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

后端常用访问地址：

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/docs`
- `http://127.0.0.1:8000/api/openapi.json`

### 4.2 启动 Frontend

推荐启动方式：

```powershell
cd D:\test\project2\owly\frontend
npm install
npm run dev
```

### 4.3 环境变量建议

不要混用 `localhost` 和 `127.0.0.1`。

建议前后端统一只使用一种主机名。

推荐使用：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`

推荐 `frontend/.env.local`：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

推荐 `backend/.env`：

```env
DATABASE_URL=postgresql://postgres:12345@localhost:5432/owly
JWT_SECRET=你的随机密钥
AUTO_CREATE_SCHEMA=false
```

---

## 5. Frontend 的运行机制

### 5.1 根布局

文件：

- `frontend/src/app/layout.tsx`

职责：

- 注册页面元信息
- 包装全局 Providers
- 引入全局样式
- 初始化主题状态

### 5.2 全局 Provider

文件：

- `frontend/src/components/providers.tsx`

当前职责：

- 目前只负责挂载 `ToastProvider`

重要历史说明：

- 在迁移早期，这里曾经做过浏览器端 `fetch` 重写
- 这种做法后来引发了认证、跨域和 cookie 问题
- 现在已经移除

维护原则：

- 不要再把 API 重写逻辑放回这里
- API 转发应继续由 Next.js 服务端代理路由处理

### 5.3 主题系统

文件：

- `frontend/src/lib/hooks/use-theme.ts`

实现方式：

- 使用 Zustand
- 使用持久化中间件
- localStorage key 为 `owly-theme`
- 同步切换 `document.documentElement.classList`

维护说明：

- 这是有意保留的纯前端状态
- 如果调整主题初始化方式，需要特别留意 hydration 行为

---

## 6. Frontend 的登录与路由控制

### 6.1 公共页面与受保护页面

文件：

- `frontend/src/proxy.ts`

当前逻辑：

- 静态资源始终允许访问
- `/api/*` 始终允许访问
- `/login` 和 `/setup` 是公开页面
- 其他页面要求存在 `owly-token` cookie

重要限制：

- `proxy.ts` 只检查 cookie 是否存在
- 它不会校验 token 是否真实有效
- 所以一个过期或失效的 cookie，仍可能让用户进入仪表盘壳页面
- 但页面中的 API 请求会被后端拒绝，返回 `401`

### 6.2 为什么之前会出现“页面能进但接口全 401”

典型问题链路：

- 浏览器中残留旧的 `owly-token`
- `proxy.ts` 看到有 cookie，于是放行进入仪表盘
- 后端验签失败，业务接口全部返回 `401`
- 页面能打开，但数据区全是报错或空白

当前已做的缓解：

- 在 `frontend/src/app/api/[...path]/route.ts` 中，如果某个非 `/api/auth` 的后端响应返回 `401`
- 前端代理层会主动清掉 `owly-token`
- 这样页面刷新后，不会继续带着失效登录态卡在仪表盘里

### 6.3 登录流程

相关文件：

- `frontend/src/app/(auth)/login/page.tsx`
- `backend/app/api/v1/auth.py`

流程：

1. 登录页先请求 `GET /api/auth`
2. 如果 `setupRequired = true`，跳转到 `/setup`
3. 表单提交 `POST /api/auth`，body 为 `{ action: "login" }`
4. 后端设置 `owly-token`
5. 浏览器通过前端代理拿到并保存 cookie
6. 前端跳转到 `/`

### 6.4 初始化流程

相关文件：

- `frontend/src/app/(auth)/setup/page.tsx`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/settings.py`

流程：

1. setup 页面请求 `GET /api/auth`
2. 第一步通过 `POST /api/auth` 创建管理员
3. 后续步骤通过 `PUT /api/settings` 保存企业配置和 AI 配置
4. 完成后跳转到仪表盘

---

## 7. API 代理层说明

### 7.1 为什么需要代理层

文件：

- `frontend/src/app/api/[...path]/route.ts`

这个代理层的目的是让前端页面代码始终只调用相对路径：

- 页面统一请求 `/api/...`
- 浏览器不直接跨域访问 backend
- cookie 从浏览器视角始终属于前端域名

### 7.2 当前代理层做了什么

当前代理层会：

- 根据 path 和 query 拼接出真正的 backend URL
- 转发请求方法、请求头、请求体
- 转发响应体和响应头
- 转发 `set-cookie`
- 删除一些不适合原样透传的传输头
- 当后端非 auth 接口返回 `401` 时，清理前端 cookie

### 7.3 维护代理层时的原则

修改 `frontend/src/app/api/[...path]/route.ts` 时：

- 保持逻辑通用
- 不要随意做某个接口的单独特殊处理
- 非必要不要改动 cookie 转发行为
- 必须保持后端状态码原样透传
- 必须保持响应体结构原样透传

如果将来再次出现登录失效、cookie 丢失、明明登录了但接口 401 等问题，这个文件应优先检查。

---

## 8. Backend 的运行机制

### 8.1 FastAPI 应用创建

文件：

- `backend/app/main.py`

职责：

- 创建 FastAPI app
- 配置 OpenAPI 文档路径
- 启用 CORS
- 注册全局异常处理
- 将总路由挂载到 `/api`

### 8.2 配置系统

文件：

- `backend/app/core/config.py`

关键配置：

- `api_v1_prefix`
- `database_url`
- `jwt_secret`
- `cors_origins`
- `auto_create_schema`

维护注意：

- 当前默认数据库仍指向 PostgreSQL
- 测试环境会覆盖为内存 SQLite
- 正常开发和部署下建议 `AUTO_CREATE_SCHEMA=false`，而不是运行时自动建表

### 8.3 总路由入口

文件：

- `backend/app/api/router.py`

这是目前后端所有已挂载 API 模块的唯一总入口。

新增一个新模块的规范步骤：

1. 在 `backend/app/api/v1/<module>.py` 新建路由文件
2. 在 `backend/app/api/router.py` 中导入
3. 用 `include_router` 挂载
4. 补测试

---

## 9. Backend 的分层模型

后端大致分为三层：

- `api`
  - 参数解析、依赖注入、响应序列化
- `domain`
  - 业务规则、schema、service
- `infrastructure`
  - 数据库模型、repository、外部集成

典型调用链：

1. `app/api/v1/*.py`
2. `app/domain/*/service.py`
3. `app/infrastructure/db/repositories/*`
4. `app/infrastructure/db/models/*`

注意：

- 当前代码并不是所有模块都严格遵守这一层次
- 有些 route 文件里还存在较多直接 ORM 操作

维护建议：

- 新改动尽量把业务逻辑往 service/repository 下沉
- route 层尽量保持薄

---

## 10. Backend 重要模块说明

### 10.1 认证模块

文件：

- `backend/app/api/v1/auth.py`

核心接口：

- `GET /api/auth`
- `POST /api/auth`
- `POST /api/auth/setup`
- `POST /api/auth/login`
- `POST /api/auth/logout`

### 10.2 仪表盘基础数据模块

文件：

- `backend/app/api/v1/conversations.py`
- `backend/app/api/v1/customers.py`
- `backend/app/api/v1/tickets.py`
- `backend/app/api/v1/team.py`
- `backend/app/api/v1/settings.py`

这些模块是页面最先依赖的数据来源。

### 10.3 运营和知识库模块

文件：

- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/business_hours.py`
- `backend/app/api/v1/sla.py`
- `backend/app/api/v1/canned_responses.py`
- `backend/app/api/v1/automation.py`

### 10.4 集成与管理模块

文件：

- `backend/app/api/v1/channels.py`
- `backend/app/api/v1/webhooks.py`
- `backend/app/api/v1/admin.py`
- `backend/app/api/v1/campaigns.py`
- `backend/app/api/v1/flows.py`
- `backend/app/api/v1/chat.py`
- `backend/app/api/v1/realtime.py`
- `backend/app/api/v1/export.py`

---

## 11. API 契约最重要的维护规则

当前项目的一个核心风险点是：接口返回风格并不完全统一。

### 11.1 有些列表接口返回数组

例如：

- `/api/team/departments`
- `/api/team/members`
- `/api/admin/users`
- `/api/admin/api-keys`
- `/api/automation`
- `/api/channels`
- `/api/webhooks`

### 11.2 有些列表接口返回分页对象

例如：

- `/api/conversations`
- `/api/customers`
- `/api/tickets`
- `/api/knowledge/categories`
- `/api/knowledge/entries`
- `/api/canned-responses`
- `/api/sla`
- `/api/campaigns`
- `/api/flows`
- `/api/activity`

典型结构如下：

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### 11.3 为什么这件事极其重要

前端之前已经多次因此出错：

- 页面以为拿到的是数组
- 实际拿到的是对象
- 结果代码里一执行 `.map`、`.filter`、`.length` 就炸

维护原则：

- 修改任何页面前，先确认真实接口返回 JSON
- 不要假设所有“列表接口”返回结构都相同

---

## 12. 目前前端已做过的契约适配

目前 `frontend` 已经在一些页面里主动适配了当前 backend 的分页返回结构。

例如：

- conversations 页面改成读 `data.data`
- customers 页面改成读 `data.data`
- tickets 页面改成读 `data.data`
- knowledge 页面改成读 `data.data`
- canned responses 页面改成读 `data.data`
- sla 页面改成读 `data.data`

这意味着：

- 如果你把某个接口从分页对象改回数组，前端也必须同步改
- 如果你想让页面恢复成原 TS 风格，后端也必须一起调整

---

## 13. 当前测试体系说明

### 13.1 Backend 测试文件

文件：

- `backend/tests/conftest.py`
- `backend/tests/test_api_contracts.py`

当前测试做了什么：

- 使用内存 SQLite 启动 FastAPI 测试环境
- 自动创建管理员、部门、成员、会话、工单、知识库、自动化规则、Webhook、Campaign、Flow、快捷回复、SLA、API Key 等种子数据
- 验证认证、仪表盘、运营、管理、报表、聊天等主要接口链路

这是一套偏“集成式 API 测试”，不是单元测试。

### 13.2 当前测试运行方式

```powershell
D:\test\project2\owly\backend\.venv\Scripts\python.exe -m pytest D:\test\project2\owly\backend\tests\test_api_contracts.py -q
```

在写这份文档时，这套测试是通过的。

### 13.3 一个重要测试注意事项

不要对以下接口使用普通阻塞式 `client.get()` 测试：

- `GET /api/realtime`

因为它是 SSE 长连接流接口，测试会像“卡住”一样不返回。

正确测试方式是测：

- `GET /api/realtime/stats`
- `POST /api/realtime/typing/{conversation_id}`

---

## 14. 常见故障模式

### 14.1 页面能打开，但接口全 401

常见原因：

- 浏览器残留失效的 `owly-token`
- 混用了 `localhost` 和 `127.0.0.1`
- backend 没有启动
- 前端代理层没有正确传递认证状态

优先检查：

- `frontend/src/app/api/[...path]/route.ts`
- 浏览器 cookie
- backend 日志
- 浏览器 network 面板中的 `/api/auth`

### 14.2 页面报 `.map is not a function` 或 `.filter is not a function`

高概率原因：

- 接口返回的是分页对象
- 页面把它当数组用了

优先检查：

- 接口真实 JSON
- 页面中的 `fetch*` 方法
- 后端 route 返回结构

### 14.3 FastAPI 出现 `ResponseValidationError`

高概率原因：

- 路由函数签名声明成 `list`
- 实际返回的是对象

这个问题之前出现在：

- conversations
- tickets
- knowledge

优先检查：

- 返回类型注解
- `response_model`
- 实际 `return` 的数据结构

### 14.4 Async SQLAlchemy 出现 `MissingGreenlet`

高概率原因：

- 在 commit 后，Pydantic 去读取延迟加载属性

优先检查：

- 某些 service 中是否直接对 ORM 对象 `model_validate`
- 是否需要先 `refresh`
- 是否应改为显式 DTO 构造

### 14.5 phone 相关接口在测试里因为 form 解析失败

高概率原因：

- `request.form()` 依赖 `python-multipart`

当前已经做过的处理：

- phone 路由支持对 URL 编码表单请求做基础解析，不再完全依赖 multipart

---

## 15. 与原 TS 项目的已知差异

当前系统已经可以运行，但还不能简单理解为“原 TS 项目 100% 原样重建”。

仍需谨慎的方向：

- AI 工作流深度
- 渠道真实接入能力
- webhook 执行语义
- 通知 UI
- 某些接口返回风格还不统一

一个典型例子：

- Header 中的通知铃铛按钮目前是静态展示
- 这和原 TS 代码一致
- 它不是迁移缺陷，而是原项目前端本来就没实现通知下拉逻辑

---

## 16. 安全修改清单

在修改任何功能前，建议按下面顺序检查：

1. 找到对应前端页面文件
2. 找到对应 backend route 文件
3. 确认接口是数组还是分页对象
4. 确认该接口是否需要认证
5. 确认 backend 是否已有测试覆盖
6. 如果接口契约变更，前后端一起改
7. 重新跑 backend 测试
8. 在浏览器中手动验证页面行为

---

## 17. 修改 Frontend 页面时的建议流程

推荐步骤：

1. 先看页面里的 `fetch*` 方法
2. 再看对应的 backend route
3. 确认页面 state 类型定义是否正确
4. 确认 loading 和 empty state 是否还能正常工作
5. 确认新增、更新、删除后页面是否会刷新

高频错误模式：

- 把整个 API 响应对象塞进数组 state

正确写法通常是：

```ts
const data: TicketListResponse = await res.json();
setTickets(data.data || []);
```

---

## 18. 修改 Backend 接口时的建议流程

推荐步骤：

1. 先看前端页面当前如何消费这个接口
2. 尽量保持已有返回字段不变
3. 尽量显式序列化，不直接返回裸 ORM
4. 如果是分页接口，返回类型和注解要一致
5. 改完补测试或改测试

尤其要小心：

- `response_model`
- 返回类型注解
- commit 后的 ORM 对象
- 时间字段序列化
- `createdAt`、`updatedAt`、`isActive` 这类别名字段

---

## 19. 建议的后续重构方向

下面这些不是立刻必须做，但会显著提升可维护性：

- 将所有列表接口统一成一种返回风格
- 抽象 frontend 的统一 API client，而不是每页都手写 `fetch`
- 给核心 dashboard 页面补前端测试
- 把 backend 测试拆分成按模块的多个文件
- 继续减少 route 层中的 ORM 直接操作
- 为 backend route 建立统一 serializer / DTO 机制
- 建立一份正式的前后端 API 契约文档

---

## 20. 常见问题时应优先查看的文件

### 20.1 认证与跳转

- `frontend/src/proxy.ts`
- `frontend/src/app/api/[...path]/route.ts`
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/setup/page.tsx`
- `backend/app/api/v1/auth.py`

### 20.2 仪表盘核心数据

- `frontend/src/app/(dashboard)/page.tsx`
- `frontend/src/app/(dashboard)/conversations/page.tsx`
- `frontend/src/app/(dashboard)/customers/page.tsx`
- `frontend/src/app/(dashboard)/tickets/page.tsx`
- `backend/app/api/v1/conversations.py`
- `backend/app/api/v1/customers.py`
- `backend/app/api/v1/tickets.py`

### 20.3 运营相关页面

- `frontend/src/app/(dashboard)/knowledge/page.tsx`
- `frontend/src/app/(dashboard)/business-hours/page.tsx`
- `frontend/src/app/(dashboard)/canned-responses/page.tsx`
- `frontend/src/app/(dashboard)/sla/page.tsx`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/business_hours.py`
- `backend/app/api/v1/canned_responses.py`
- `backend/app/api/v1/sla.py`

### 20.4 代理与环境问题

- `frontend/.env.example`
- `backend/.env.example`
- `backend/app/core/config.py`
- `frontend/next.config.ts`

---

## 21. 最后给维护者的实用建议

- 前后端改动尽量成对进行
- 不要假设所有列表接口返回结构一致
- 出现登录异常时，优先从 cookie / 代理层排查
- 页面出现 `.map/.filter is not a function` 时，优先怀疑响应结构不一致
- 出现 `ResponseValidationError` 时，优先检查 route 的类型声明和真实返回值
- 每次修改重要 API 后都应重新跑 backend 测试
- 每次改动认证逻辑后，都应在浏览器里做一次真实登录流程验证

只要后续维护者遵循这份文档里的这些原则，当前这套拆分后的前后端系统虽然仍带有迁移时期的历史包袱，但依然是可维护、可继续迭代的。
