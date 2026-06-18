# Auth 模块对比文档

本文档对比分析 `src` (TypeScript/Next.js) 与 `backend` (Python/FastAPI) 中认证模块的实现差异。

## 1. 架构概览

### TypeScript (src) 架构

```
src/
├── lib/
│   └── auth.ts              # 核心认证逻辑
├── app/api/auth/
│   └── route.ts             # API 端点
└── app/(auth)/
    ├── login/page.tsx       # 登录页面
    └── setup/page.tsx       # 初始化设置页面
```

### Python (backend) 架构

```
backend/app/
├── domain/auth/
│   ├── schemas.py           # 数据模型
│   └── service.py           # 业务逻辑
├── api/v1/
│   └── auth.py              # API 端点
├── core/
│   └── security.py          # 安全工具（密码哈希、JWT）
└── infrastructure/db/
    ├── models/auth.py       # 数据库模型
    └── repositories/auth.py # 数据访问层
```

## 2. 功能对比

| 功能 | TypeScript | Python | 状态 |
|------|------------|--------|------|
| 密码哈希 | bcryptjs | passlib/bcrypt | ✅ 一致 |
| JWT 生成 | jsonwebtoken | python-jose | ✅ 一致 |
| Cookie 认证 | owly-token | owly-token | ✅ 一致 |
| 初始化设置 | setup action | /setup 端点 | ✅ 一致 |
| 登录 | login action | /login 端点 | ✅ 一致 |
| 登出 | logout action | /logout 端点 | ✅ 一致 |
| API Key 认证 | ❌ 无 | ✅ 支持 | 🆕 增强 |

## 3. 核心代码对比

### 3.1 密码哈希

**TypeScript (`src/lib/auth.ts`):**
```typescript
import bcrypt from "bcryptjs";

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 12);
}

export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

**Python (`backend/app/core/security.py`):**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**差异分析:**
- 两者都使用 bcrypt 算法
- TypeScript 使用 `bcryptjs` 库，rounds=12
- Python 使用 `passlib` 库，自动处理 rounds

### 3.2 JWT Token

**TypeScript (`src/lib/auth.ts`):**
```typescript
import jwt from "jsonwebtoken";

const JWT_SECRET = getJwtSecret();
const TOKEN_EXPIRY = "7d";

export function generateToken(userId: string, role: string): string {
  return jwt.sign({ userId, role }, JWT_SECRET, { expiresIn: TOKEN_EXPIRY });
}

export function verifyToken(token: string): { userId: string; role: string } | null {
  try {
    return jwt.verify(token, JWT_SECRET) as { userId: string; role: string };
  } catch {
    return null;
  }
}
```

**Python (`backend/app/core/security.py`):**
```python
from datetime import timedelta
from jose import jwt

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def decode_access_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return TokenData(user_id=payload.get("sub"), role=payload.get("role"))
    except JWTError:
        return None
```

**差异分析:**
- TypeScript 使用 `userId` 作为 payload key
- Python 使用标准的 `sub` (subject) claim
- 两者都使用 HS256 算法，7天过期时间

### 3.3 API 端点

**TypeScript (`src/app/api/auth/route.ts`):**
```typescript
// POST /api/auth - 统一端点，通过 action 区分
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { action, username, password, name } = body;

  if (action === "setup") {
    // 初始化设置逻辑
  }
  if (action === "login") {
    // 登录逻辑
  }
  if (action === "logout") {
    // 登出逻辑
  }
}

// GET /api/auth - 检查认证状态
export async function GET() {
  const setupDone = await isSetupComplete();
  const user = await getCurrentUser();
  return NextResponse.json({ authenticated: !!user, setupRequired: !setupDone, user });
}
```

**Python (`backend/app/api/v1/auth.py`):**
```python
# 分离的端点设计
@router.get("", response_model=AuthStatusResponse)
async def auth_status(request: Request, session: AsyncSession = Depends(get_session)):
    # 检查认证状态
    ...

@router.post("/setup")
async def setup(payload: SetupRequest, response: Response, session: AsyncSession = Depends(get_session)):
    # 初始化设置
    ...

@router.post("/login")
async def login(payload: LoginRequest, response: Response, session: AsyncSession = Depends(get_session)):
    # 登录
    ...

@router.post("/logout")
async def logout(response: Response):
    # 登出
    ...

# 兼容原有 API 格式
@router.post("")
async def auth_action(payload: AuthActionRequest, ...):
    if payload.action == "setup":
        return await setup(...)
    if payload.action == "login":
        return await login(...)
    if payload.action == "logout":
        return await logout(...)
```

**差异分析:**
- Python 采用 RESTful 风格的分离端点
- 同时保留兼容原有 action 格式的统一端点
- Python 使用 Pydantic 模型进行请求验证

## 4. 工作流程对比

### 4.1 初始化设置流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     初始化设置流程                               │
├─────────────────────────────────────────────────────────────────┤
│ TypeScript                          Python                      │
│ ───────────                         ──────                      │
│ 1. POST /api/auth                   1. POST /api/v1/auth/setup  │
│    {action: "setup"}                   {username, password}     │
│                                                                 │
│ 2. 检查是否已初始化                  2. 检查是否已初始化          │
│    isSetupComplete()                  admin_repo.count()        │
│                                                                 │
│ 3. 创建 Admin 用户                   3. 创建 Admin 用户          │
│    prisma.admin.create()              admin_repo.add()          │
│                                                                 │
│ 4. 初始化默认设置                    4. 初始化默认设置           │
│    prisma.settings.upsert()           settings_repo.ensure()    │
│                                                                 │
│ 5. 初始化默认渠道                    5. 初始化默认渠道           │
│    prisma.channel.upsert()            settings_repo.ensure()    │
│                                                                 │
│ 6. 生成 JWT Token                   6. 生成 JWT Token          │
│    generateToken()                    create_access_token()     │
│                                                                 │
│ 7. 设置 Cookie                       7. 设置 Cookie             │
│    response.cookies.set()             response.set_cookie()     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 登录流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        登录流程                                  │
├─────────────────────────────────────────────────────────────────┤
│ TypeScript                          Python                      │
│ ───────────                         ──────                      │
│ 1. POST /api/auth                   1. POST /api/v1/auth/login  │
│    {action: "login"}                   {username, password}     │
│                                                                 │
│ 2. 查找用户                         2. 查找用户                  │
│    prisma.admin.findUnique()          admin_repo.get_by_username()│
│                                                                 │
│ 3. 验证密码                         3. 验证密码                  │
│    verifyPassword()                   verify_password()         │
│                                                                 │
│ 4. 生成 Token                       4. 生成 Token               │
│    generateToken()                    create_access_token()     │
│                                                                 │
│ 5. 设置 Cookie                       5. 设置 Cookie             │
│    response.cookies.set()             response.set_cookie()     │
└─────────────────────────────────────────────────────────────────┘
```

## 5. 新增功能

### 5.1 API Key 认证 (Python 独有)

Python 版本新增了 API Key 认证支持：

```python
# backend/app/domain/auth/service.py
async def authenticate_api_key(self, raw_key: str) -> AuthContext | None:
    api_key = await self.api_key_repo.get_active(raw_key)
    if not api_key:
        return None
    await self.api_key_repo.touch_last_used(api_key.id)
    return AuthContext(
        user_id=f"api-key:{api_key.id}",
        username=api_key.name,
        name=api_key.name,
        role=Role.ADMIN,
        auth_method="api_key",
    )
```

使用方式：
```python
# 通过 X-API-Key header 认证
@router.get("/protected")
async def protected_route(auth: AuthContext = Depends(get_auth_context)):
    ...
```

## 6. 数据模型对比

### Admin 用户模型

**TypeScript (Prisma):**
```prisma
model Admin {
  id       String @id @default(cuid())
  username String @unique
  password String
  name     String
  role     String @default("admin")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

**Python (SQLAlchemy):**
```python
class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(50), default="admin")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

## 7. 依赖注入对比

**TypeScript:**
```typescript
// 直接使用 Prisma Client
import { prisma } from "@/lib/prisma";

const admin = await prisma.admin.findUnique({ where: { username } });
```

**Python:**
```python
# 使用依赖注入和 Repository 模式
from app.api.deps import get_session
from app.infrastructure.db.repositories.auth import AdminRepository

@router.post("/login")
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    service = AuthService(
        admin_repo=AdminRepository(session),
        api_key_repo=ApiKeyRepository(session),
    )
    user = await service.login(payload)
```

## 8. 总结

| 方面 | TypeScript | Python |
|------|------------|--------|
| 架构风格 | 单文件集中式 | 分层架构 (API/Service/Repository) |
| 数据验证 | 手动验证 | Pydantic 模型 |
| 数据库访问 | Prisma Client | SQLAlchemy + Repository |
| 依赖注入 | 无 | FastAPI Depends |
| API Key 支持 | ❌ | ✅ |
| 测试友好性 | 中等 | 高 (易于 mock) |

Python 版本在保持功能一致性的同时，采用了更清晰的分层架构，便于测试和维护。
