from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class UserCreate(BaseModel):
    """
    Internal schema for creating or synchronizing
    a Clerk user in PostgreSQL.
    """

    clerk_user_id: str = Field(
        min_length=1,
        max_length=255,
    )

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    display_name: str = Field(
        min_length=1,
        max_length=100,
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator(
        "clerk_user_id",
        "username",
        "display_name",
    )
    @classmethod
    def strip_text_fields(
        cls,
        value: str,
    ) -> str:
        return value.strip()


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator(
        "username",
        "display_name",
    )
    @classmethod
    def strip_optional_text_fields(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip()


class UserSummary(BaseModel):
    id: UUID
    username: str
    display_name: str
    avatar_url: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserResponse(BaseModel):
    id: UUID
    clerk_user_id: str
    username: str
    display_name: str
    avatar_url: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserSearchResponse(BaseModel):
    users: list[UserSummary]