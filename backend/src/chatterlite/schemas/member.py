from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from chatterlite.models.enums import MemberRole
from chatterlite.schemas.user import UserSummary


class AddConversationMembersRequest(BaseModel):
    user_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("user_ids")
    @classmethod
    def remove_duplicate_user_ids(
        cls,
        user_ids: list[UUID],
    ) -> list[UUID]:
        unique_user_ids = list(
            dict.fromkeys(user_ids)
        )

        return unique_user_ids


class UpdateMemberRoleRequest(BaseModel):
    role: MemberRole


class ConversationMemberResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    user_id: UUID
    role: MemberRole

    last_read_message_id: UUID | None
    last_read_at: datetime | None

    is_muted: bool

    joined_at: datetime
    left_at: datetime | None

    user: UserSummary

    model_config = ConfigDict(
        from_attributes=True,
    )