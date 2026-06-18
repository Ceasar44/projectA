# TS 原始 API 与 Python Backend API 对照清单

说明:

- `TS` 指原 `src/app/api/**/route.ts`
- `Python` 指当前 `backend/app/api/v1/*.py`
- 状态说明:
  - `已实现且基本对齐`
  - `已实现但仍有差异`
  - `Python 额外扩展`
  - `TS 有但 Python 未见独立实现`

## 1. 认证 `auth`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/auth` | 有 | 有 | 已实现且基本对齐 | 返回登录状态与 setupRequired |
| `POST /api/auth` | 有 | 有 | 已实现且基本对齐 | 统一处理 setup/login/logout |
| `POST /api/auth/setup` | 无 | 有 | Python 额外扩展 | Python 提供了显式路径 |
| `POST /api/auth/login` | 无 | 有 | Python 额外扩展 | Python 提供了显式路径 |
| `POST /api/auth/logout` | 无 | 有 | Python 额外扩展 | Python 提供了显式路径 |

## 2. 设置 `settings`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/settings` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/settings` | 有 | 有 | 已实现且基本对齐 |  |

## 3. 会话 `conversations`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/conversations` | 有 | 有 | 已实现且基本对齐 | 已收敛为分页包 |
| `POST /api/conversations` | 有 | 有 | 已实现且基本对齐 | 创建校验已对齐为 400 |
| `GET /api/conversations/{id}` | 有 | 有 | 已实现但仍有差异 | Python 已补 `customer/tickets`，仍建议继续核对细节 |
| `PUT /api/conversations/{id}` | 有 | 有 | 已实现但仍有差异 | 需继续核对标签、状态边界与副作用 |
| `DELETE /api/conversations/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/conversations/{id}/messages` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/messages` | 有 | 有 | 已实现但仍有差异 | 已接自动化，但仍需继续核对副作用顺序 |
| `GET /api/conversations/{id}/notes` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/notes` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/transfer` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/merge` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/snooze` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/satisfaction` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/route-to` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/conversations/{id}/macro` | 有 | 有 | 已实现但仍有差异 | 宏动作的完整业务闭环仍建议继续核对 |

## 4. AI 对话 `chat`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `POST /api/chat` | 有 | 有 | 已实现但仍有差异 | 路径和主返回已接近，完整 AI 工作流仍未完全 1:1 |

## 5. 客户 `customers`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/customers` | 有 | 有 | 已实现且基本对齐 | 已收敛为分页包 |
| `POST /api/customers` | 有 | 有 | 已实现且基本对齐 | 创建校验已收敛 |
| `GET /api/customers/{id}` | 有 | 有 | 已实现但仍有差异 | 会话匹配和历史拼装建议继续核对 |
| `PUT /api/customers/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/customers/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/customers/{id}/notes` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/customers/{id}/notes` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/customers/{id}/conversations` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/customers/{id}/gdpr/export` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/customers/{id}/gdpr/delete` | 有 | 有 | 已实现且基本对齐 |  |

## 6. 工单 `tickets`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/tickets` | 有 | 有 | 已实现且基本对齐 | 已收敛为分页包 |
| `POST /api/tickets` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/tickets/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/tickets/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/tickets/{id}` | 有 | 有 | 已实现且基本对齐 |  |

## 7. 知识库 `knowledge`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/knowledge/categories` | 有 | 有 | 已实现且基本对齐 | 已收敛为分页包 |
| `POST /api/knowledge/categories` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/knowledge/categories/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/knowledge/categories/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/knowledge/entries` | 有 | 有 | 已实现且基本对齐 | 已收敛为分页包 |
| `POST /api/knowledge/entries` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/knowledge/entries/{id}` | 有 | 有 | 已实现且基本对齐 | 404 文案已对齐 |
| `DELETE /api/knowledge/entries/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/knowledge/test` | 有 | 有 | 已实现但仍有差异 | 错误分支和结构已接近，真实 AI 测试流程仍未完全等价 |

## 8. 团队 `team`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/team/departments` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/team/departments` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/team/departments/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/team/departments/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/team/members` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/team/members` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/team/members/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/team/members/{id}` | 有 | 有 | 已实现且基本对齐 |  |

## 9. 自动化 `automation`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/automation` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/automation` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/automation/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/automation/{id}` | 有 | 有 | 已实现且基本对齐 |  |

## 10. 营业时间 `business-hours`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/business-hours` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/business-hours` | 有 | 有 | 已实现且基本对齐 |  |

## 11. SLA `sla`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/sla` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/sla` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/sla/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/sla/{id}` | 有 | 有 | 已实现且基本对齐 |  |

## 12. 快捷回复 `canned-responses`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/canned-responses` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/canned-responses` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/canned-responses/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/canned-responses/{id}` | 有 | 有 | 已实现且基本对齐 |  |

## 13. 渠道 `channels`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/channels` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/channels` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/channels/{type}` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/channels/{type}` | 有 | 有 | 已实现但仍有差异 | 兼容路由已补，但真实渠道行为仍非完全等价 |
| `GET /api/channels/email` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/channels/email` | 有 | 有 | 已实现但仍有差异 | 当前更偏状态联调，不是完整 Email listener |
| `POST /api/channels/sms` | 有 | 有 | 已实现但仍有差异 | 主要由通用动态路由兜底 |
| `POST /api/channels/telegram` | 有 | 有 | 已实现但仍有差异 | 主要由通用动态路由兜底 |
| `GET /api/channels/whatsapp` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/channels/whatsapp` | 有 | 有 | 已实现但仍有差异 | 真实 WhatsApp SDK 行为尚未完全复刻 |
| `POST /api/channels/phone/incoming` | 有 | 有 | 已实现且基本对齐 | 已补来电入口 |
| `POST /api/channels/phone/gather` | 有 | 有 | 已实现且基本对齐 | 已补语音输入回调 |
| `POST /api/channels/phone/status` | 有 | 有 | 已实现且基本对齐 | 已补通话状态回调 |

## 14. Webhooks `webhooks`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/webhooks` | 有 | 有 | 已实现但仍有差异 | Python 列表接口仍建议收敛为分页包以完全对齐 |
| `POST /api/webhooks` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/webhooks/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/webhooks/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/webhooks/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/webhooks/test` | 有 | 有 | 已实现但仍有差异 | 已很接近，真实 delivery 行为仍需继续核对 |
| `GET /api/webhooks/{id}/deliveries` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/webhooks/{id}/deliveries` | 有 | 有 | 已实现且基本对齐 | TS 兼容路径已补 |
| `POST /api/webhooks/{id}/deliveries/{deliveryId}/retry` | 无 | 有 | Python 额外扩展 | 额外提供了更显式的 retry 路径 |

## 15. Campaigns `campaigns`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/campaigns` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/campaigns` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/campaigns/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/campaigns/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/campaigns/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/campaigns/{id}/execute` | 有 | 有 | 已实现且基本对齐 | Python 已补目标客群计算逻辑 |

## 16. Flows `flows`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/flows` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/flows` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/flows/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/flows/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/flows/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/flows/{id}/validate` | 有 | 有 | 已实现且基本对齐 | Python 已补节点验证逻辑 |

## 17. 管理后台 `admin`

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/admin/users` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/admin/users` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/admin/users/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/admin/users/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/admin/api-keys` | 有 | 有 | 已实现且基本对齐 |  |
| `POST /api/admin/api-keys` | 有 | 有 | 已实现且基本对齐 |  |
| `PUT /api/admin/api-keys/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `DELETE /api/admin/api-keys/{id}` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/admin/plugins` | 有 | 有 | 已实现且基本对齐 |  |

## 18. 分析与统计

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/analytics` | 有 | 有 | 已实现但仍有差异 | 建议继续逐字段核对 |
| `GET /api/stats` | 有 | 有 | 已实现且基本对齐 | 扁平 totals 已对齐 |
| `GET /api/activity` | 有 | 有 | 已实现且基本对齐 | 已收掉额外子路由 |

## 19. 导出与实时

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/export` | 有 | 有 | 已实现且基本对齐 | 已收掉额外 export 子路由 |
| `GET /api/realtime` | 有 | 有 | 已实现但仍有差异 | Python SSE 事件包装仍建议继续收敛 |

## 20. 其他

| 接口 | TS | Python | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| `GET /api/health` | 有 | 有 | 已实现且基本对齐 |  |
| `GET /api/openapi.json` | 有 | 有 | 已实现且基本对齐 | Python 由 FastAPI `openapi_url` 提供 |

## 总结

### 基本结论

- TS 原始 API 的主要路径，Python backend 现在几乎都已经覆盖。
- 大部分 CRUD 接口已经达到“已实现且基本对齐”。
- 剩下最主要的差异集中在“执行型工作流”，而不是“有没有这个路由”。

### 当前仍建议重点关注的接口

- `POST /api/chat`
- `POST /api/knowledge/test`
- `POST /api/channels/email`
- `POST /api/channels/whatsapp`
- `POST /api/channels/sms`
- `POST /api/channels/telegram`
- `GET /api/realtime`
- `POST /api/webhooks/test`

这些接口现在更多是“可联调、可兼容”，但还不一定是对 TS 运行态行为的完全复刻。

