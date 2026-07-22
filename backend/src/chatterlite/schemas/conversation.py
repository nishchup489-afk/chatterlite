from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from chatterlite.models.enums import ConversationType
from chatterlite.schemas.member import (
    ConversationMemberResponse,
)
from chatterlite.schemas.message import MessagePreview


class DirectConversationCreate(BaseModel):
    user_id: UUID


class GroupConversationCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )

    member_ids: list[UUID] = Field(
        min_length=1,
        max_length=99,
    )

    @field_validator("title")
    @classmethod
    def clean_title(
        cls,
        title: str,
    ) -> str:
        cleaned_title = title.strip()

        if not cleaned_title:
            raise ValueError(
                "Group title cannot be empty."
            )

        return cleaned_title

    @field_validator("member_ids")
    @classmethod
    def remove_duplicate_member_ids(
        cls,
        member_ids: list[UUID],
    ) -> list[UUID]:
        return list(
            dict.fromkeys(member_ids)
        )


class ConversationUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    image_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator("title")
    @classmethod
    def clean_optional_title(
        cls,
        title: str | None,
    ) -> str | None:
        if title is None:
            return None

        cleaned_title = title.strip()

        if not cleaned_title:
            raise ValueError(
                "Group title cannot be empty."
            )

        return cleaned_title

    @model_validator(mode="after")
    def reject_empty_update(
        self,
    ) -> "ConversationUpdate":
        if (
            self.title is None
            and self.image_url is None
        ):
            raise ValueError(
                "At least one field must be provided."
            )

        return self


class ConversationSummary(BaseModel):
    id: UUID
    type: ConversationType
    title: str | None
    image_url: str | None

    last_message: MessagePreview | None

    unread_count: int = 0

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ConversationResponse(BaseModel):
    id: UUID
    type: ConversationType

    title: str | None
    image_url: str | None

    created_by: UUID

    members: list[
        ConversationMemberResponse
    ]

    last_message: MessagePreview | None

    unread_count: int = 0

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ConversationListResponse(BaseModel):
    items: list[ConversationSummary]

    next_cursor: str | None = None

    has_more: bool = False