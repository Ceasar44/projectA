from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.customer.schemas import CustomerCreate, CustomerDetail, CustomerListResponse, CustomerUpdate


class CustomerService:
    def __init__(self, customer_repo, note_repo, conversation_repo, uow):
        self.customer_repo = customer_repo
        self.note_repo = note_repo
        self.conversation_repo = conversation_repo
        self.uow = uow

    async def list_customers(self, page: int, limit: int, search: str | None):
        items, total = await self.customer_repo.list(page, limit, search)
        return CustomerListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_customer(self, payload: CustomerCreate) -> CustomerDetail:
        customer = await self.customer_repo.create(payload)
        await self.uow.commit()
        return CustomerDetail.model_validate(customer)

    async def get_customer(self, customer_id: str) -> CustomerDetail:
        customer = await self.customer_repo.get(customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return CustomerDetail.model_validate(customer)

    async def update_customer(self, customer_id: str, payload: CustomerUpdate) -> CustomerDetail:
        customer = await self.customer_repo.update(customer_id, payload)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        await self.uow.commit()
        return CustomerDetail.model_validate(customer)

    async def delete_customer(self, customer_id: str) -> dict[str, bool]:
        if not await self.customer_repo.delete(customer_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        await self.uow.commit()
        return {"success": True}

    async def list_notes(self, customer_id: str) -> list[dict[str, object]]:
        return [
            {"id": note.id, "content": note.content, "authorName": note.author_name, "createdAt": note.created_at}
            for note in await self.note_repo.list(customer_id)
        ]

    async def create_note(self, customer_id: str, content: str, author_name: str = "Admin") -> dict[str, object]:
        note = await self.note_repo.add(customer_id, content, author_name)
        await self.uow.commit()
        return {"id": note.id, "content": note.content, "authorName": note.author_name, "createdAt": note.created_at}
