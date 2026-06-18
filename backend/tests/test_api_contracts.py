def test_auth_and_public_routes(client) -> None:
    auth_status = client.get("/api/auth")
    assert auth_status.status_code == 200
    assert auth_status.json()["setupRequired"] is True

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    openapi = client.get("/api/openapi.json")
    assert openapi.status_code == 200


def test_dashboard_resource_crud(authed_client, seed_data) -> None:
    conversations = authed_client.get("/api/conversations?limit=10")
    assert conversations.status_code == 200, conversations.text
    conversations_payload = conversations.json()
    assert "data" in conversations_payload
    assert "pagination" in conversations_payload
    assert conversations_payload["data"][0]["id"] == seed_data["conversation_id"]

    conversation_detail = authed_client.get(f"/api/conversations/{seed_data['conversation_id']}")
    assert conversation_detail.status_code == 200, conversation_detail.text
    assert "tickets" in conversation_detail.json()

    transfer = authed_client.post(
        f"/api/conversations/{seed_data['conversation_id']}/transfer",
        json={"toMemberId": seed_data["member_id"], "note": "Please take this"},
    )
    assert transfer.status_code == 200, transfer.text
    assert transfer.json()["success"] is True

    note = authed_client.post(
        f"/api/conversations/{seed_data['conversation_id']}/notes",
        json={"content": "Internal note"},
    )
    assert note.status_code == 201, note.text

    customers = authed_client.get("/api/customers?page=1&limit=20")
    assert customers.status_code == 200, customers.text
    customers_payload = customers.json()
    assert "data" in customers_payload
    assert "pagination" in customers_payload

    customer_detail = authed_client.get(f"/api/customers/{seed_data['customer_id']}")
    assert customer_detail.status_code == 200, customer_detail.text
    assert "notes" in customer_detail.json()
    assert "conversations" in customer_detail.json()

    customer_note = authed_client.post(
        f"/api/customers/{seed_data['customer_id']}/notes",
        json={"content": "VIP customer", "authorName": "Admin"},
    )
    assert customer_note.status_code == 200, customer_note.text

    customer_conversations = authed_client.get(
        f"/api/customers/{seed_data['customer_id']}/conversations"
    )
    assert customer_conversations.status_code == 200, customer_conversations.text
    assert "data" in customer_conversations.json()

    gdpr_export = authed_client.get(f"/api/customers/{seed_data['customer_id']}/gdpr/export")
    assert gdpr_export.status_code == 200, gdpr_export.text
    assert gdpr_export.json()["customer"]["id"] == seed_data["customer_id"]

    tickets = authed_client.get("/api/tickets")
    assert tickets.status_code == 200, tickets.text
    assert "data" in tickets.json()

    ticket_detail = authed_client.get(f"/api/tickets/{seed_data['ticket_id']}")
    assert ticket_detail.status_code == 200, ticket_detail.text
    assert ticket_detail.json()["department"]["id"] == seed_data["department_id"]

    ticket_update = authed_client.put(
        f"/api/tickets/{seed_data['ticket_id']}",
        json={"status": "in_progress"},
    )
    assert ticket_update.status_code == 200, ticket_update.text
    assert ticket_update.json()["status"] == "in_progress"


def test_knowledge_and_ops_modules(authed_client, seed_data) -> None:
    business_hours = authed_client.get("/api/business-hours")
    assert business_hours.status_code == 200, business_hours.text
    assert business_hours.json()["id"] == "default"

    business_hours_update = authed_client.put(
        "/api/business-hours",
        json={"enabled": True, "timezone": "Asia/Shanghai"},
    )
    assert business_hours_update.status_code == 200, business_hours_update.text
    assert business_hours_update.json()["enabled"] is True

    categories = authed_client.get("/api/knowledge/categories")
    assert categories.status_code == 200, categories.text
    assert "data" in categories.json()

    entries = authed_client.get("/api/knowledge/entries")
    assert entries.status_code == 200, entries.text
    assert "data" in entries.json()

    entry_toggle = authed_client.put(
        f"/api/knowledge/entries/{seed_data['entry_id']}",
        json={"isActive": False},
    )
    assert entry_toggle.status_code == 200, entry_toggle.text
    assert entry_toggle.json()["isActive"] is False

    knowledge_test = authed_client.post("/api/knowledge/test", json={"question": "How do I greet users?"})
    assert knowledge_test.status_code in {200, 400}, knowledge_test.text

    automation_rules = authed_client.get("/api/automation")
    assert automation_rules.status_code == 200, automation_rules.text
    assert isinstance(automation_rules.json(), list)

    canned_responses = authed_client.get("/api/canned-responses")
    assert canned_responses.status_code == 200, canned_responses.text
    canned_payload = canned_responses.json()
    assert "data" in canned_payload
    assert canned_payload["data"][0]["id"] == seed_data["canned_response_id"]

    canned_categories = authed_client.get("/api/canned-responses/categories")
    assert canned_categories.status_code == 200, canned_categories.text
    assert "General" in canned_categories.json()

    canned_shortcut = authed_client.get("/api/canned-responses/shortcut/welcome")
    assert canned_shortcut.status_code == 200, canned_shortcut.text

    sla = authed_client.get("/api/sla")
    assert sla.status_code == 200, sla.text
    assert "data" in sla.json()

    sla_detail = authed_client.get(f"/api/sla/{seed_data['sla_rule_id']}")
    assert sla_detail.status_code == 200, sla_detail.text
    assert sla_detail.json()["id"] == seed_data["sla_rule_id"]


def test_admin_channels_campaigns_and_webhooks(authed_client, seed_data) -> None:
    users = authed_client.get("/api/admin/users")
    assert users.status_code == 200, users.text
    assert isinstance(users.json(), list)

    new_user = authed_client.post(
        "/api/admin/users",
        json={"username": "agent", "password": "password123", "name": "Agent", "role": "admin"},
    )
    assert new_user.status_code == 201, new_user.text

    api_keys = authed_client.get("/api/admin/api-keys")
    assert api_keys.status_code == 200, api_keys.text
    assert isinstance(api_keys.json(), list)

    plugins = authed_client.get("/api/admin/plugins")
    assert plugins.status_code == 200, plugins.text

    departments = authed_client.get("/api/team/departments")
    assert departments.status_code == 200, departments.text
    assert isinstance(departments.json(), list)

    members = authed_client.get("/api/team/members")
    assert members.status_code == 200, members.text
    assert isinstance(members.json(), list)

    channels = authed_client.get("/api/channels")
    assert channels.status_code == 200, channels.text
    assert isinstance(channels.json(), list)

    save_channel = authed_client.post(
        "/api/channels",
        json={"type": "email", "config": {"host": "smtp.example.com"}, "isActive": True},
    )
    assert save_channel.status_code == 200, save_channel.text

    email_status = authed_client.get("/api/channels/email")
    assert email_status.status_code == 200, email_status.text

    phone_status = authed_client.post("/api/channels/phone/status", data={"CallSid": "abc123"})
    assert phone_status.status_code == 200, phone_status.text

    campaigns = authed_client.get("/api/campaigns")
    assert campaigns.status_code == 200, campaigns.text
    assert "data" in campaigns.json()

    execute_campaign = authed_client.post(f"/api/campaigns/{seed_data['campaign_id']}/execute")
    assert execute_campaign.status_code == 200, execute_campaign.text
    assert execute_campaign.json()["campaignId"] == seed_data["campaign_id"]
    assert "targetCount" in execute_campaign.json()

    flows = authed_client.get("/api/flows")
    assert flows.status_code == 200, flows.text
    assert "data" in flows.json()

    validate_flow = authed_client.post(f"/api/flows/{seed_data['flow_id']}/validate")
    assert validate_flow.status_code == 200, validate_flow.text
    assert "valid" in validate_flow.json()

    webhooks = authed_client.get("/api/webhooks")
    assert webhooks.status_code == 200, webhooks.text
    assert isinstance(webhooks.json(), list)

    webhook_detail = authed_client.get(f"/api/webhooks/{seed_data['webhook_id']}")
    assert webhook_detail.status_code == 200, webhook_detail.text

    deliveries = authed_client.get(f"/api/webhooks/{seed_data['webhook_id']}/deliveries")
    assert deliveries.status_code == 200, deliveries.text
    assert "data" in deliveries.json()


def test_reporting_and_misc_endpoints(authed_client, seed_data) -> None:
    settings = authed_client.get("/api/settings")
    assert settings.status_code == 200, settings.text
    assert settings.json()["id"] == "default"

    stats = authed_client.get("/api/stats")
    assert stats.status_code == 200, stats.text
    assert "totalConversations" in stats.json()

    analytics_stats = authed_client.get("/api/stats")
    assert analytics_stats.status_code == 200, analytics_stats.text

    analytics = authed_client.get("/api/analytics?period=30d")
    assert analytics.status_code == 200, analytics.text
    assert analytics.json()["period"] == "30d"

    activity_prefixed = authed_client.get("/api/activity?page=1&limit=20")
    assert activity_prefixed.status_code == 200, activity_prefixed.text
    assert "activities" in activity_prefixed.json()

    activity_global = authed_client.get("/api/activity?entity=conversation")
    assert activity_global.status_code == 200, activity_global.text

    export_json = authed_client.get("/api/export?type=conversations&format=json")
    assert export_json.status_code == 200, export_json.text
    assert export_json.headers["content-type"].startswith("application/json")

    realtime_stats = authed_client.get("/api/realtime/stats")
    assert realtime_stats.status_code == 200, realtime_stats.text
    assert "subscriberCount" in realtime_stats.json()

    typing = authed_client.post(
        f"/api/realtime/typing/{seed_data['conversation_id']}",
        json={"userName": "Agent", "isTyping": True},
    )
    assert typing.status_code == 200, typing.text
    assert typing.json()["success"] is True

    chat = authed_client.post(
        "/api/chat",
        json={
            "message": "Hello, I need help with my order",
            "conversationId": seed_data["conversation_id"],
            "channel": "email",
            "customerContact": "bob@example.com",
        },
    )
    assert chat.status_code == 200, chat.text
    assert chat.json()["conversationId"] == seed_data["conversation_id"]


def test_customer_support_agent_chat_contract(authed_client, seed_data) -> None:
    chat = authed_client.post(
        "/api/chat",
        json={
            "message": "Hello, can you help me understand your greeting policy?",
            "conversationId": seed_data["conversation_id"],
            "channel": "email",
            "customerContact": "bob@example.com",
        },
    )
    assert chat.status_code == 200, chat.text
    payload = chat.json()
    assert payload["conversationId"] == seed_data["conversation_id"]
    assert payload["response"]
    assert payload["status"] in {"sent", "escalated"}
    assert isinstance(payload["confidence"], float)
    assert payload["intent"]
    assert payload["sentiment"]
    assert "toolCalls" in payload

    detail = authed_client.get(f"/api/conversations/{seed_data['conversation_id']}")
    assert detail.status_code == 200, detail.text
    assert len(detail.json()["messages"]) >= 3


def test_customer_support_agent_escalates_sensitive_requests(authed_client, seed_data) -> None:
    chat = authed_client.post(
        "/api/chat",
        json={
            "message": "I want a refund immediately or I will call my attorney.",
            "conversationId": seed_data["conversation_id"],
            "channel": "email",
            "customerContact": "bob@example.com",
        },
    )
    assert chat.status_code == 200, chat.text
    payload = chat.json()
    assert payload["status"] == "escalated"
    assert payload["intent"] in {"refund", "human_handoff"}
    assert payload["escalationReason"]

    detail = authed_client.get(f"/api/conversations/{seed_data['conversation_id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "escalated"


def test_customer_support_agent_can_create_ticket_from_chat(authed_client, seed_data) -> None:
    conversation = authed_client.post(
        "/api/conversations",
        json={
            "channel": "email",
            "customerName": "Carol",
            "customerContact": "carol@example.com",
        },
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]

    chat = authed_client.post(
        "/api/chat",
        json={
            "message": "The app is broken and not working. Please create a ticket for technical support.",
            "conversationId": conversation_id,
            "channel": "email",
            "customerContact": "carol@example.com",
        },
    )
    assert chat.status_code == 200, chat.text
    payload = chat.json()
    assert payload["conversationId"] == conversation_id
    assert any(call["name"] == "create_ticket" for call in payload["toolCalls"])

    tickets = authed_client.get("/api/tickets")
    assert tickets.status_code == 200, tickets.text
    assert any(item["conversationId"] == conversation_id for item in tickets.json()["data"])
