from sqlalchemy import func, select

from app.domain.flows.schemas import FlowCreate, FlowRead, FlowUpdate
from app.infrastructure.db.models.operations import Flow


class FlowRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, is_active: bool | None):
        filters = []
        if is_active is not None:
            filters.append(Flow.is_active == is_active)
        stmt = select(Flow).where(*filters).order_by(Flow.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(Flow).where(*filters)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [FlowRead.model_validate(row) for row in rows], total

    async def create(self, payload: FlowCreate) -> Flow:
        item = Flow(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, flow_id: str) -> Flow | None:
        return await self.session.get(Flow, flow_id)

    async def update(self, flow_id: str, payload: FlowUpdate) -> Flow | None:
        item = await self.get(flow_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete(self, flow_id: str) -> bool:
        item = await self.get(flow_id)
        if not item:
            return False
        await self.session.delete(item)
        return True

    async def validate(self, flow_id: str) -> dict[str, object]:
        item = await self.get(flow_id)
        if not item:
            return {"valid": False, "errors": ["Flow not found"]}
        errors: list[str] = []
        nodes = item.nodes or []
        node_ids = {str(node.get("id", "")) for node in nodes if node.get("id")}

        if not item.start_node_id:
            errors.append("Flow must have a start node")
        elif item.start_node_id not in node_ids:
            errors.append("Start node ID does not exist")

        for node in nodes:
            node_id = str(node.get("id", ""))
            next_node_id = node.get("nextNodeId")
            if next_node_id and next_node_id not in node_ids:
                errors.append(f'Node {node_id}: nextNodeId "{next_node_id}" does not exist')

            for option in node.get("options", []) or []:
                option_next = option.get("nextNodeId")
                if option_next and option_next not in node_ids:
                    errors.append(
                        f'Node {node_id}: option "{option.get("label", "")}" points to non-existent node'
                    )

            condition = node.get("condition") or {}
            if condition:
                if condition.get("trueNodeId") not in node_ids:
                    errors.append(f"Node {node_id}: condition trueNodeId does not exist")
                if condition.get("falseNodeId") not in node_ids:
                    errors.append(f"Node {node_id}: condition falseNodeId does not exist")

        reachable: set[str] = set()
        queue: list[str] = [item.start_node_id] if item.start_node_id else []
        by_id = {str(node.get("id", "")): node for node in nodes}
        while queue:
            current_id = queue.pop(0)
            if current_id in reachable:
                continue
            reachable.add(current_id)
            node = by_id.get(current_id)
            if not node:
                continue
            if node.get("nextNodeId"):
                queue.append(str(node["nextNodeId"]))
            for option in node.get("options", []) or []:
                if option.get("nextNodeId"):
                    queue.append(str(option["nextNodeId"]))
            condition = node.get("condition") or {}
            if condition.get("trueNodeId"):
                queue.append(str(condition["trueNodeId"]))
            if condition.get("falseNodeId"):
                queue.append(str(condition["falseNodeId"]))

        unreachable = [str(node.get("id", "")) for node in nodes if str(node.get("id", "")) not in reachable]
        if unreachable:
            errors.append(f"Unreachable nodes: {', '.join(unreachable)}")
        return {"valid": len(errors) == 0, "errors": errors}
