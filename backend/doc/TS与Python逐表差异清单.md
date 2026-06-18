# TS 与 Python 逐表差异清单

说明:

- TS 指原 `prisma/schema.prisma`
- Python 指 `backend/app/infrastructure/db/models/*.py`
- 本清单聚焦“表是否存在、字段是否大体对应、当前主要差异、后续建议”

## 1. `settings`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 字段命名风格不同，TS 为 `camelCase`，Python 为 `snake_case` |
| 备注 | 结构整体接近 |
| 建议 | 继续保持数据库列与 API alias 对齐，重点核对默认值与迁移脚本 |

## 2. `admin`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `role` 在 Python 中绑定枚举语义，但数据库仍存字符串 |
| 备注 | 结构接近 |
| 建议 | 核对默认 role、长度、唯一索引与密码字段长度 |

## 3. `api_key`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 仅命名风格差异，如 `isActive` / `is_active` |
| 备注 | 基本一致 |
| 建议 | 核对唯一约束与索引迁移是否完整 |

## 4. `category`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `sortOrder` / `sort_order` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对排序默认值和 `_count.entries` 查询语义 |

## 5. `knowledge_entry`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `metadata` 在 Python 属性名是 `metadata_json`，数据库列仍映射为 `metadata` |
| 备注 | 结构接近 |
| 建议 | 核对 `version` 自增逻辑和 `category` 关联查询一致性 |

## 6. `department`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 仅命名风格不同 |
| 备注 | 基本一致 |
| 建议 | 核对删除级联和 team/ticket 关联的外键迁移 |

## 7. `team_member`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `isAvailable` / `is_available` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对 `department_id` 外键与索引 |

## 8. `conversation`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 命名风格不同；`metadata` 在 Python 属性名是 `metadata_json` |
| 备注 | 核心字段齐全 |
| 建议 | 继续核对索引、状态枚举范围、标签和客户关联工作流 |

## 9. `message`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `mediaType` / `media_type`，`toolCalls` / `tool_calls` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对 `(conversationId, createdAt)` 复合索引是否在迁移中补齐 |

## 10. `ticket`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 仅命名风格不同 |
| 备注 | 基本一致 |
| 建议 | 核对外键、索引、状态默认值、关联查询 include 语义 |

## 11. `tag`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 大体是 |
| 当前主要差异 | Python 当前 `color` 默认值为空字符串，TS 默认 `#4A7C9B`；Python 模型未在 `models/__init__.py` 导出 |
| 备注 | 结构已建，但整合不完整 |
| 建议 | 对齐默认值，并加入统一模型导出 |

## 12. `conversation_tag`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 大体是 |
| 当前主要差异 | Python 代码片段中未见显式声明 TS 的 `@@unique([conversationId, tagId])`；也未在 `models/__init__.py` 导出 |
| 备注 | 这是一个重点差异 |
| 建议 | 显式补唯一约束，并纳入统一导出与迁移 |

## 13. `call_log`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | Python 属性名为 `from_number` / `to_number`，但数据库列仍映射为 `from` / `to` |
| 备注 | 这是实现层命名差异，不是表结构硬差异 |
| 建议 | 核对唯一约束 `callSid` 和电话流程落库逻辑 |

## 14. `channel`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 命名风格不同 |
| 备注 | 基本一致 |
| 建议 | 核对默认值、唯一约束和渠道初始化数据 |

## 15. `schedule`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 基本是 |
| 当前主要差异 | 目前 Python 只补了模型与迁移，尚未补基于 `schedule` 的业务接入 |
| 备注 | 结构层差距已补齐 |
| 建议 | 后续再按需要补 repository/service/API |

## 16. `webhook`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `triggerOn` / `trigger_on` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对投递行为与实际 delivery 状态语义 |

## 17. `webhook_delivery`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 命名风格差异，如 `statusCode` / `status_code` |
| 备注 | 字段基本齐全 |
| 建议 | 核对 `(status, nextRetryAt)` 索引与重试 worker 是否补齐 |

## 18. `activity_log`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | Python 使用 `metadata_json` 属性映射 `metadata` 列 |
| 备注 | 基本一致 |
| 建议 | 核对索引、查询参数和审计写入路径 |

## 19. `sla_rule`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 命名风格差异，如 `firstResponseMins` / `first_response_mins` |
| 备注 | 基本一致 |
| 建议 | 核对默认值和 API alias 完整性 |

## 20. `canned_response`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `usageCount` / `usage_count` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对默认值与使用次数自增逻辑 |

## 21. `customer`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 命名风格差异；`metadata` 在 Python 属性名是 `metadata_json` |
| 备注 | 核心字段齐全 |
| 建议 | 核对客户归并逻辑是否充分利用这些字段 |

## 22. `customer_note`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 仅命名风格不同 |
| 备注 | 基本一致 |
| 建议 | 核对创建、列表排序与作者默认值 |

## 23. `automation_rule`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `triggerCount` / `trigger_count` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对规则触发链路和触发次数更新是否与 TS 完全一致 |

## 24. `business_hours`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 基本是 |
| 当前主要差异 | `offlineMessage` / `offline_message` 命名差异；默认文案与 TS 不完全一致 |
| 备注 | 有轻微默认值偏差 |
| 建议 | 对齐默认文案 |

## 25. `internal_note`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | 仅命名风格不同 |
| 备注 | 基本一致 |
| 建议 | 核对索引、创建逻辑和返回结构 |

## 26. `campaign`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `scheduledAt` / `scheduled_at`，`sentCount` / `sent_count` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对状态迁移与发送执行链路 |

## 27. `flow`

| 项目 | 结论 |
| --- | --- |
| TS 是否存在 | 是 |
| Python 是否存在 | 是 |
| 字段是否基本对应 | 是 |
| 当前主要差异 | `startNodeId` / `start_node_id`，`triggerCount` / `trigger_count` 命名差异 |
| 备注 | 基本一致 |
| 建议 | 核对校验逻辑与运行态执行引擎 |

## 总结

### 当前最关键的结构差异

- 表级缺失已补齐
- 剩余重点转为约束、默认值、迁移落库和业务接入的一致性

### 当前最关键的实现差异

- `tag` 和 `conversation_tag` 虽然已有模型，但导出与约束仍需补齐
- 少数默认值未完全对齐:
  - `tag.color`
  - `business_hours.offline_message`

### 如果要做到数据库层 1:1 复刻，优先建议

1. 用真实 PostgreSQL 凭据完成在线 Alembic `upgrade head`
2. 核对并验证 `conversation_tag` 唯一约束已成功落库
3. 核对 `tag` / `conversation_tag` 已纳入统一导出与 metadata
4. 验证少量默认值已按预期落库
5. 再补 `schedule` 的 repository/service/API（如果业务需要）
