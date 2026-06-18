import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "true")

from app.main import create_app  # noqa: E402


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def authed_client(client: TestClient) -> TestClient:
    response = client.post(
        "/api/auth",
        json={
            "action": "setup",
            "username": "admin",
            "password": "password123",
            "name": "Admin",
        },
    )
    assert response.status_code == 200, response.text
    return client


@pytest.fixture()
def seed_data(authed_client: TestClient) -> dict[str, str]:
    department = authed_client.post(
        "/api/team/departments",
        json={"name": "Support", "description": "Help desk", "email": "support@example.com"},
    )
    assert department.status_code == 201, department.text
    department_id = department.json()["id"]

    member = authed_client.post(
        "/api/team/members",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "departmentId": department_id,
            "role": "lead",
            "expertise": "billing,refund",
        },
    )
    assert member.status_code == 201, member.text
    member_id = member.json()["id"]

    conversation = authed_client.post(
        "/api/conversations",
        json={
            "channel": "email",
            "customerName": "Bob",
            "customerContact": "bob@example.com",
        },
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]

    message = authed_client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "hello", "role": "customer"},
    )
    assert message.status_code == 201, message.text

    customers = authed_client.get("/api/customers")
    assert customers.status_code == 200, customers.text
    customer_id = customers.json()["data"][0]["id"]

    ticket = authed_client.post(
        "/api/tickets",
        json={
            "title": "Need help",
            "departmentId": department_id,
            "assignedToId": member_id,
            "conversationId": conversation_id,
        },
    )
    assert ticket.status_code == 201, ticket.text
    ticket_id = ticket.json()["id"]

    category = authed_client.post("/api/knowledge/categories", json={"name": "General"})
    assert category.status_code == 201, category.text
    category_id = category.json()["id"]

    entry = authed_client.post(
        "/api/knowledge/entries",
        json={
            "categoryId": category_id,
            "title": "Greeting",
            "content": "Hello there",
        },
    )
    assert entry.status_code == 201, entry.text
    entry_id = entry.json()["id"]

    automation = authed_client.post(
        "/api/automation",
        json={
            "name": "Auto assign",
            "description": "Route customer messages",
            "type": "message_received",
            "isActive": True,
            "conditions": [{"field": "channel", "operator": "equals", "value": "email"}],
            "actions": [{"action": "add_tag", "tag": "email"}],
            "priority": 1,
        },
    )
    assert automation.status_code == 201, automation.text
    automation_id = automation.json()["id"]

    webhook = authed_client.post(
        "/api/webhooks",
        json={
            "name": "Order Webhook",
            "description": "Notify external system",
            "url": "https://example.com/webhook",
            "method": "POST",
            "headers": {"X-Test": "1"},
            "isActive": True,
            "triggerOn": "ticket.created",
        },
    )
    assert webhook.status_code == 201, webhook.text
    webhook_id = webhook.json()["id"]

    campaign = authed_client.post(
        "/api/campaigns",
        json={
            "name": "Spring Campaign",
            "channel": "email",
            "message": "Hello customers",
            "subject": "Promo",
            "segments": [],
        },
    )
    assert campaign.status_code == 201, campaign.text
    campaign_id = campaign.json()["id"]

    flow = authed_client.post(
        "/api/flows",
        json={
            "name": "Support Flow",
            "description": "Simple support flow",
            "startNodeId": "start",
            "nodes": [
                {"id": "start", "type": "message", "data": {"text": "Hello"}, "nextNodeId": "end"},
                {"id": "end", "type": "end", "data": {}},
            ],
            "isActive": True,
        },
    )
    assert flow.status_code == 201, flow.text
    flow_id = flow.json()["id"]

    canned_response = authed_client.post(
        "/api/canned-responses",
        json={
            "title": "Welcome",
            "content": "Welcome to Owly",
            "category": "General",
            "shortcut": "welcome",
            "isActive": True,
        },
    )
    assert canned_response.status_code == 201, canned_response.text
    canned_response_id = canned_response.json()["id"]

    sla_rule = authed_client.post(
        "/api/sla",
        json={
            "name": "Default SLA",
            "description": "Standard response target",
            "channel": "all",
            "priority": "all",
            "firstResponseMins": 30,
            "resolutionMins": 480,
            "isActive": True,
        },
    )
    assert sla_rule.status_code == 201, sla_rule.text
    sla_rule_id = sla_rule.json()["id"]

    api_key = authed_client.post(
        "/api/admin/api-keys",
        json={"name": "Integration Key"},
    )
    assert api_key.status_code == 201, api_key.text
    api_key_id = api_key.json()["id"]

    return {
        "department_id": department_id,
        "member_id": member_id,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "ticket_id": ticket_id,
        "category_id": category_id,
        "entry_id": entry_id,
        "automation_id": automation_id,
        "webhook_id": webhook_id,
        "campaign_id": campaign_id,
        "flow_id": flow_id,
        "canned_response_id": canned_response_id,
        "sla_rule_id": sla_rule_id,
        "api_key_id": api_key_id,
    }
