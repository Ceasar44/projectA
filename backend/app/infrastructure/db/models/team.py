import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


class Department(Base):
    __tablename__ = "department"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    email: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    members: Mapped[list["TeamMember"]] = relationship(back_populates="department")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="department")


class TeamMember(Base):
    __tablename__ = "team_member"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(300))
    phone: Mapped[str] = mapped_column(String(50), default="")
    role: Mapped[str] = mapped_column(String(100), default="member")
    expertise: Mapped[str] = mapped_column(String(500), default="")
    department_id: Mapped[str] = mapped_column(ForeignKey("department.id", ondelete="CASCADE"), index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    department: Mapped[Department] = relationship(back_populates="members")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="assigned_to")


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversation.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id: Mapped[str | None] = mapped_column(ForeignKey("department.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id: Mapped[str | None] = mapped_column(ForeignKey("team_member.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    resolution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    conversation: Mapped["Conversation | None"] = relationship(back_populates="tickets")
    department: Mapped[Department | None] = relationship(back_populates="tickets")
    assigned_to: Mapped[TeamMember | None] = relationship(back_populates="tickets")


class Schedule(Base):
    __tablename__ = "schedule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_member_id: Mapped[str] = mapped_column(String(36), index=True)
    day_of_week: Mapped[int] = mapped_column(index=True)
    start_time: Mapped[str] = mapped_column(String(20))
    end_time: Mapped[str] = mapped_column(String(20))
