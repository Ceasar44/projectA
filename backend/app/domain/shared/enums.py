from enum import StrEnum


class Role(StrEnum):
    VIEWER = "viewer"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ChannelType(StrEnum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    TELEGRAM = "telegram"
    API = "api"
    WIDGET = "widget"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
    SNOOZED = "snoozed"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
