# RAG 模块

## 业务流程

### 知识库管理

1. 管理端创建 `knowledge_base`，并初始化向量库 collection。
2. 可创建 `knowledge_category`，上传文件到分类形成 `knowledge_category_file`。
3. 文件进入知识库后写入 `knowledge_file`。

### 文档处理

1. 上传文档或从分类启动切片任务。
2. 创建 `knowledge_job`，记录任务状态、阶段和进度。
3. 文档被解析成多个 `knowledge_chunk`。
4. 原始切片内容写入 `knowledge_chunk_origin`，图片关联写入 `knowledge_chunk_image`。
5. 清洗、编辑、回滚后可将切片 upsert 到向量库。
6. 如果启用 `sync_graph`，可同步知识图谱并查询图谱结果。

### RAG 问答

1. 用户创建或复用 `conversation_session`。
2. 调用知识问答接口，系统执行查询改写、分类、检索、过滤、重排、生成、质量检查。
3. 问答消息写入 `conversation_message`，保存来源、置信度和图片占位符。
4. 流式接口通过 SSE 输出生成过程。

## 领域对象与关系

- `RagKnowledgeBase`：RAG 知识库。
- `RagKnowledgeCategory`：RAG 分类。
- `RagKnowledgeCategoryFile`：分类文件。
- `RagKnowledgeFile`：进入知识库处理的文件。
- `RagKnowledgeJob`：切片/向量化任务。
- `RagKnowledgeChunk`：文本切片。
- `RagKnowledgeChunkOrigin`：切片原文。
- `RagKnowledgeChunkImage`：切片图片。
- `RagConversationSession`：RAG 会话。
- `RagConversationMessage`：RAG 消息。

关系说明：

- `knowledge_base.id` 1 对多 `knowledge_file.kb_id`。
- `knowledge_base.id` 1 对多 `knowledge_job.kb_id`。
- `knowledge_category.id` 1 对多 `knowledge_category_file.category_id`。
- `knowledge_category_file.id` 1 对多 `knowledge_file.category_file_id`。
- `knowledge_file.id` 1 对多 `knowledge_job.file_id`。
- `knowledge_job.id` 1 对多 `knowledge_chunk.job_id`。
- `knowledge_chunk.id` 1 对 1 `knowledge_chunk_origin.chunk_id`。
- `knowledge_chunk.id` 1 对多 `knowledge_chunk_image.chunk_id`。
- `conversation_session.id` 1 对多 `conversation_message.session_id`。
- `conversation_session.kb_name` 业务上关联 `knowledge_base.name`，但没有外键。

## 状态机

### 文件处理状态

```text
pending
  ├─ 开始处理 -> processing
  ├─ 处理成功 -> completed
  └─ 处理失败 -> failed
```

### 任务状态

```text
pending
  ├─ parsing -> processing
  ├─ chunking -> processing
  ├─ cleaning -> processing
  ├─ upsert -> vectorizing
  ├─ 完成 -> completed
  └─ 失败 -> failed
completed
  └─ upsert -> vectorized=true
```

### 切片状态

```text
original
  ├─ edit/clean -> modified
modified
  └─ revert -> original
```

### RAG 会话

```text
created
  ├─ 用户提问 -> active
  ├─ AI 回答 -> active
  └─ delete -> deleted
```

## 模块结构

- `backend/app/rag/api/v1/*`：RAG API。
- `backend/app/rag/services/*`：文档、切片、检索、问答、文件、任务、知识图谱服务。
- `backend/app/rag/db/repositories.py`：RAG 仓储集合。
- `backend/app/infrastructure/db/models/rag.py`：RAG 数据模型。
- `backend/app/rag_agents/knowledge/*`：RAG Agent 图和节点。
- `backend/app/rag/core/*`：RAG 配置、异常、日志、提示词。
- `backend/app/rag/bootstrap.py`：RAG 运行时初始化和关闭。
