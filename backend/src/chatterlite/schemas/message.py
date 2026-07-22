from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from chatterlite.models.enums import MessageType
from chatterlite.schemas.user import UserSummary


class MessageCreate(BaseModel):
    client_message_id: UUID

    content: str = Field(
        min_length=1,
        max_length=4000,
    )

    reply_to_message_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        content: str,
    ) -> str:
        cleaned_content = content.strip()

        if not cleaned_content:
            raise ValueError(
                "Message content cannot be empty."
            )

        return cleaned_content


class MarkConversationReadRequest(BaseModel):
    message_id: UUID


class MessagePreview(BaseModel):
    id: UUID
    sender_id: UUID
    content: str | None
    message_type: MessageType
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    client_message_id: UUID

    message_type: MessageType
    content: str | None

    reply_to_message_id: UUID | None

    created_at: datetime
    edited_at: datetime | None
    deleted_at: datetime | None

    sender: UserSummary

    model_config = ConfigDict(
        from_attributes=True,
    )


class MessageListResponse(BaseModel):
    items: list[MessageResponse]

    next_cursor: str | None = None

    has_more: bool = False