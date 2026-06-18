from datetime import UTC, datetime

from sqlalchemy import func, or_, select

from app.domain.customer.schemas import CustomerCreate, CustomerSummary, CustomerUpdate
from app.infrastructure.db.models.conversations import Customer, CustomerNote


def normalize_phone(value: str) -> str:
    cleaned = value.replace("@c.us", "").replace("@s.whatsapp.net", "")
    return "".join(ch for ch in cleaned if ch.isdigit() or ch == "+")


class CustomerRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, search: str | None):
        filters = []
        if search:
            like = f"%{search}%"
            filters.append(
                or_(
                    Customer.name.ilike(like),
                    Customer.email.ilike(like),
                    Customer.phone.ilike(like),
                    Customer.whatsapp.ilike(like),
                )
            )
        stmt = select(Customer).where(*filters).order_by(Customer.last_contact.desc()).offset((page - 1) * limit).limit(limit)
        total_stmt = select(func.count()).select_from(Customer).where(*filters)
        rows = (await self.session.scalars(stmt)).all()
        total = await self.session.scalar(total_stmt) or 0
        return [CustomerSummary.model_validate(row) for row in rows], total

    async def create(self, payload: CustomerCreate) -> Customer:
        customer = Customer(**payload.model_dump(by_alias=False))
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def get(self, customer_id: str) -> Customer | None:
        return await self.session.get(Customer, customer_id)

    async def update(self, customer_id: str, payload: CustomerUpdate) -> Customer | None:
        customer = await self.get(customer_id)
        if not customer:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(customer, field, value)
        customer.last_contact = datetime.now(UTC)
        await self.session.flush()
        return customer

    async def delete(self, customer_id: str) -> bool:
        customer = await self.get(customer_id)
        if not customer:
            return False
        await self.session.delete(customer)
        return True

    async def resolve_customer(self, channel: str, customer_contact: str, customer_name: str) -> str:
        if not customer_contact:
            customer = Customer(name=customer_name or "Unknown", first_contact=datetime.now(UTC), last_contact=datetime.now(UTC))
            self.session.add(customer)
            await self.session.flush()
            return customer.id

        customer = None
        if channel == "email":
            customer = await self.session.scalar(select(Customer).where(Customer.email.ilike(customer_contact)))
        elif channel == "phone":
            customer = await self.session.scalar(select(Customer).where(Customer.phone == customer_contact))
        elif channel == "whatsapp":
            customer = await self.session.scalar(select(Customer).where(Customer.whatsapp == customer_contact))
        if not customer and channel in {"phone", "whatsapp"}:
            normalized = normalize_phone(customer_contact)
            if len(normalized) >= 7:
                customer = await self.session.scalar(
                    select(Customer).where(
                        or_(Customer.phone.contains(normalized), Customer.whatsapp.contains(normalized))
                    )
                )
        if not customer:
            customer = await self.session.scalar(
                select(Customer).where(
                    or_(
                        Customer.email.ilike(customer_contact),
                        Customer.phone == customer_contact,
                        Customer.whatsapp == customer_contact,
                    )
                )
            )
        if not customer:
            customer = Customer(name=customer_name or "Unknown", first_contact=datetime.now(UTC), last_contact=datetime.now(UTC))
            if channel == "email":
                customer.email = customer_contact
            elif channel == "phone":
                customer.phone = customer_contact
            elif channel == "whatsapp":
                customer.whatsapp = customer_contact
            self.session.add(customer)
            await self.session.flush()
            return customer.id

        customer.last_contact = datetime.now(UTC)
        if channel == "email" and not customer.email:
            customer.email = customer_contact
        elif channel == "phone" and not customer.phone:
            customer.phone = customer_contact
        elif channel == "whatsapp" and not customer.whatsapp:
            customer.whatsapp = customer_contact
        if customer.name == "Unknown" and customer_name and customer_name != "Unknown":
            customer.name = customer_name
        await self.session.flush()
        return customer.id


class CustomerNoteRepository:
    def __init__(self, session):
        self.session = session

    async def add(self, customer_id: str, content: str, author_name: str) -> CustomerNote:
        note = CustomerNote(customer_id=customer_id, content=content, author_name=author_name)
        self.session.add(note)
        await self.session.flush()
        return note

    async def list(self, customer_id: str) -> list[CustomerNote]:
        stmt = select(CustomerNote).where(CustomerNote.customer_id == customer_id).order_by(CustomerNote.created_at.desc())
        return list((await self.session.scalars(stmt)).all())
