from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.automation.schemas import (
    AutomationRuleCreate,
    AutomationRuleListResponse,
    AutomationRuleRead,
    AutomationRuleUpdate,
)


class AutomationService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def list_rules(self, page: int, limit: int, is_active: bool | None):
        items, total = await self.repo.list(page, limit, is_active)
        return AutomationRuleListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_rule(self, payload: AutomationRuleCreate) -> AutomationRuleRead:
        item = await self.repo.create(payload)
        await self.uow.commit()
        return AutomationRuleRead.model_validate(item)

    async def update_rule(self, rule_id: str, payload: AutomationRuleUpdate) -> AutomationRuleRead:
        item = await self.repo.update(rule_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")
        await self.uow.commit()
        return AutomationRuleRead.model_validate(item)

    async def delete_rule(self, rule_id: str) -> dict[str, bool]:
        deleted = await self.repo.delete(rule_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")
        await self.uow.commit()
        return {"success": True}

    async def evaluate_rules(self, message: dict[str, str], conversation: dict[str, str]) -> list[dict[str, object]]:
        rules = await self.repo.list_active()
        matched_actions: list[dict[str, object]] = []

        for rule in rules:
            conditions = rule.conditions or []
            if not conditions:
                continue
            if all(self._evaluate_condition(condition, message, conversation) for condition in conditions):
                matched_actions.append(
                    {
                        "ruleId": rule.id,
                        "ruleName": rule.name,
                        "type": rule.type,
                        "actions": rule.actions or [],
                    }
                )
                await self.repo.increment_trigger_count(rule.id)

        if matched_actions:
            await self.uow.commit()
        return matched_actions

    def _evaluate_condition(self, condition: dict, message: dict[str, str], conversation: dict[str, str]) -> bool:
        field_value = self._get_field_value(str(condition.get("field", "")), message, conversation).lower()
        target_value = str(condition.get("value", "")).lower()
        operator = str(condition.get("operator", ""))

        if operator == "contains":
            return target_value in field_value
        if operator == "equals":
            return field_value == target_value
        if operator == "starts_with":
            return field_value.startswith(target_value)
        return False

    def _get_field_value(self, field: str, message: dict[str, str], conversation: dict[str, str]) -> str:
        if field == "message_content":
            return message.get("content", "")
        if field == "channel":
            return message.get("channel", "") or conversation.get("channel", "")
        if field == "customer_name":
            return message.get("customerName", "") or conversation.get("customerName", "")
        return ""
