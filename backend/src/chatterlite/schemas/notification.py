from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from chatterlite.models.enums import NotificationType
from chatterlite.schemas.user import UserSummary


class NotificationResponse(BaseModel):
    id: UUID

    recipient_id: UUID
    actor_id: UUID | None

    type: NotificationType

    conversation_id: UUID | None
    message_id: UUID | None

    title: str
    body: str

    is_read: bool

    created_at: datetime
    read_at: datetime | None

    actor: UserSummary | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]

    next_cursor: str | None = None

    has_more: bool = False


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationReadResponse(BaseModel):
    id: UUID
    is_read: bool
    read_at: datetime | None