# 业务知识库模块 Knowledge

## 业务流程

1. 管理员创建知识分类。
2. 管理员在分类下创建知识条目，设置优先级和启用状态。
3. 前端按分类或分页查询知识条目。
4. 客服 Agent、AI 工作台或测试接口读取启用的知识条目。
5. 管理员可更新或删除条目；删除分类会级联删除其条目。
6. `POST /api/knowledge/test` 用当前知识库内容测试问答效果。

## 领域对象与关系

- `Category`：业务知识分类。
- `KnowledgeEntry`：业务知识条目。
- `KnowledgeService`：分类和条目的 CRUD 服务。
- `CategoryCreate`、`EntryCreate`、`EntryRead`：知识库 DTO。

关系说明：

- `category.id` 1 对多 `knowledge_entry.category_id`。
- `knowledge_entry.id` 会以 JSON 数组形式被 AI 工作台表引用，如 `knowledge_entry_ids`，但不是数据库外键。

## 状态机

### 知识条目启用状态

```text
active
  └─ is_active=false -> inactive
inactive
  └─ is_active=true -> active
```

### 知识条目版本

```text
version=1
  └─ 更新内容 -> version 可递增或保持，当前模型提供字段但业务层主要覆盖更新
```

## 模块结构

- `backend/app/api/v1/knowledge.py`：知识库 API。
- `backend/app/domain/knowledge/service.py`：知识分类和条目服务。
- `backend/app/domain/knowledge/schemas.py`：知识库 schema。
- `backend/app/infrastructure/db/models/knowledge.py`：`Category`、`KnowledgeEntry`。
- `backend/app/infrastructure/db/repositories/knowledge.py`：知识库仓储。
