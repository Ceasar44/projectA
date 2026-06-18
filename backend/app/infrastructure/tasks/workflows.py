from app.infrastructure.events.types import DomainEvent
from app.infrastructure.tasks.ports import TaskQueue


class WorkflowDispatcher:
    def __init__(self, queue: TaskQueue):
        self.queue = queue

    async def dispatch_from_event(self, event: DomainEvent) -> str:
        mapping = {
            "conversation.created": "sync_conversation_metrics",
            "message.received": "evaluate_automation_rules",
            "webhook.delivery.failed": "retry_webhook_delivery",
        }
        task_name = mapping.get(event.name, "noop")
        return await self.queue.enqueue(task_name, event.payload)
