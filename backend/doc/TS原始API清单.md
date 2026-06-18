# TS 原始 API 清单

说明:

- 本文档基于 `src/app/api/**/route.ts` 整理。
- 仅描述原 TS/Next.js 后端中定义的 API。
- 路径统一写为对外访问形式 `/api/...`。

## 1. 认证 `auth`

- `GET /api/auth`
- `POST /api/auth`

## 2. 设置 `settings`

- `GET /api/settings`
- `PUT /api/settings`

## 3. 会话 `conversations`

- `GET /api/conversations`
- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `PUT /api/conversations/{id}`
- `DELETE /api/conversations/{id}`
- `GET /api/conversations/{id}/messages`
- `POST /api/conversations/{id}/messages`
- `GET /api/conversations/{id}/notes`
- `POST /api/conversations/{id}/notes`
- `POST /api/conversations/{id}/transfer`
- `POST /api/conversations/{id}/merge`
- `POST /api/conversations/{id}/snooze`
- `POST /api/conversations/{id}/satisfaction`
- `POST /api/conversations/{id}/route-to`
- `POST /api/conversations/{id}/macro`

## 4. AI 对话 `chat`

- `POST /api/chat`

## 5. 客户 `customers`

- `GET /api/customers`
- `POST /api/customers`
- `GET /api/customers/{id}`
- `PUT /api/customers/{id}`
- `DELETE /api/customers/{id}`
- `GET /api/customers/{id}/notes`
- `POST /api/customers/{id}/notes`
- `GET /api/customers/{id}/conversations`
- `GET /api/customers/{id}/gdpr/export`
- `DELETE /api/customers/{id}/gdpr/delete`

## 6. 工单 `tickets`

- `GET /api/tickets`
- `POST /api/tickets`
- `GET /api/tickets/{id}`
- `PUT /api/tickets/{id}`
- `DELETE /api/tickets/{id}`

## 7. 知识库 `knowledge`

- `GET /api/knowledge/categories`
- `POST /api/knowledge/categories`
- `PUT /api/knowledge/categories/{id}`
- `DELETE /api/knowledge/categories/{id}`
- `GET /api/knowledge/entries`
- `POST /api/knowledge/entries`
- `PUT /api/knowledge/entries/{id}`
- `DELETE /api/knowledge/entries/{id}`
- `POST /api/knowledge/test`

## 8. 团队 `team`

- `GET /api/team/departments`
- `POST /api/team/departments`
- `PUT /api/team/departments/{id}`
- `DELETE /api/team/departments/{id}`
- `GET /api/team/members`
- `POST /api/team/members`
- `PUT /api/team/members/{id}`
- `DELETE /api/team/members/{id}`

## 9. 自动化 `automation`

- `GET /api/automation`
- `POST /api/automation`
- `PUT /api/automation/{id}`
- `DELETE /api/automation/{id}`

## 10. 营业时间 `business-hours`

- `GET /api/business-hours`
- `PUT /api/business-hours`

## 11. SLA `sla`

- `GET /api/sla`
- `POST /api/sla`
- `PUT /api/sla/{id}`
- `DELETE /api/sla/{id}`

## 12. 快捷回复 `canned-responses`

- `GET /api/canned-responses`
- `POST /api/canned-responses`
- `PUT /api/canned-responses/{id}`
- `DELETE /api/canned-responses/{id}`

## 13. 渠道 `channels`

- `GET /api/channels`
- `POST /api/channels`
- `GET /api/channels/{type}`
- `POST /api/channels/{type}`
- `GET /api/channels/email`
- `POST /api/channels/email`
- `POST /api/channels/sms`
- `POST /api/channels/telegram`
- `GET /api/channels/whatsapp`
- `POST /api/channels/whatsapp`
- `POST /api/channels/phone/incoming`
- `POST /api/channels/phone/gather`
- `POST /api/channels/phone/status`

## 14. Webhooks `webhooks`

- `GET /api/webhooks`
- `POST /api/webhooks`
- `GET /api/webhooks/{id}`
- `PUT /api/webhooks/{id}`
- `DELETE /api/webhooks/{id}`
- `POST /api/webhooks/test`
- `GET /api/webhooks/{id}/deliveries`
- `POST /api/webhooks/{id}/deliveries`

## 15. Campaigns `campaigns`

- `GET /api/campaigns`
- `POST /api/campaigns`
- `GET /api/campaigns/{id}`
- `PUT /api/campaigns/{id}`
- `DELETE /api/campaigns/{id}`
- `POST /api/campaigns/{id}/execute`

## 16. Flows `flows`

- `GET /api/flows`
- `POST /api/flows`
- `GET /api/flows/{id}`
- `PUT /api/flows/{id}`
- `DELETE /api/flows/{id}`
- `POST /api/flows/{id}/validate`

## 17. 管理后台 `admin`

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PUT /api/admin/users/{id}`
- `DELETE /api/admin/users/{id}`
- `GET /api/admin/api-keys`
- `POST /api/admin/api-keys`
- `PUT /api/admin/api-keys/{id}`
- `DELETE /api/admin/api-keys/{id}`
- `GET /api/admin/plugins`

## 18. 分析与统计

- `GET /api/analytics`
- `GET /api/stats`
- `GET /api/activity`

## 19. 导出与实时

- `GET /api/export`
- `GET /api/realtime`

## 20. 其他

- `GET /api/health`
- `GET /api/openapi.json`

