from typing import Protocol


class TaskQueue(Protocol):
    async def enqueue(self, task_name: str, payload: dict) -> str: ...


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self.jobs: list[dict] = []

    async def enqueue(self, task_name: str, payload: dict) -> str:
        job = {"task_name": task_name, "payload": payload}
        self.jobs.append(job)
        return str(len(self.jobs))
