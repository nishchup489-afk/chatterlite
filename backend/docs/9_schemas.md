# Next Step — Pydantic Schemas

Schemas define the **data entering and leaving your API**.

```text
SQLAlchemy models → PostgreSQL structure
Pydantic schemas  → API request/response structure
```

Schemas should not contain:

```text
SQLAlchemy columns
Database relationships
Database queries
commit()
Redis logic
WebSocket connections
```

They should contain:

```text
Validation
Request bodies
Response shapes
Pagination structures
Reusable nested API objects
```

---

# 1. Recommended structure

```text
src/
└── chatterlite/
    └── schemas/
        ├── __init__.py
        ├── common.py
        ├── user.py
        ├── member.py
        ├── message.py
        ├── conversation.py
        └── notification.py
```

Do not create these yet:

```text
presence.py
websocket.py
```

Add them during the presence and WebSocket phases. No need to build tomorrow’s machinery today.

---

# 2. Naming convention

Use predictable names:

```text
SomethingCreate      Request for creating something
SomethingUpdate      Request for updating something
SomethingResponse    API response
SomethingSummary     Smaller nested response
SomethingListResponse Paginated list response
```

Avoid unclear names like:

```text
UserSchema
ConversationSchema
MessageData
```

Those names do not explain whether the schema is input or output.

---

# 3. `schemas/common.py`

Create:

```text
src/chatterlite/schemas/common.py
```

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class CursorPage(BaseModel, Generic[DataT]):
    items: list[DataT]

    next_cursor: str | None = None

    has_more: bool = False


class PaginationQuery(BaseModel):
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    cursor: str | None = None
```

## Why this exists

Instead of redefining pagination repeatedly:

```python
class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None
    has_more: bool
```

You can use:

```python
CursorPage[MessageResponse]
```

---

# 4. `schemas/user.py`

Create:

```text
src/chatterlite/schemas/user.py
```

```python
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
```

## `from_attributes=True`

This allows Pydantic to convert a SQLAlchemy object:

```python
user_schema = UserResponse.model_validate(
    user_model
)
```

Without it, Pydantic expects a dictionary.

---

# 5. `schemas/member.py`

Create:

```text
src/chatterlite/schemas/member.py
```

```python
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
```

The service still decides whether the authenticated user is allowed to add, remove, promote, or demote members.

Schemas validate shape. They do not enforce business permissions.

---

# 6. `schemas/message.py`

Create:

```text
src/chatterlite/schemas/message.py
```

```python
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
```

## Why `conversation_id` is not inside `MessageCreate`

Your REST endpoint should look like:

```http
POST /api/v1/conversations/{conversation_id}/messages
```

The conversation ID comes from the URL path.

Request body:

```json
{
  "client_message_id": "69bca90f-5631-44ee-8260-f7c783d62e13",
  "content": "Hello",
  "reply_to_message_id": null
}
```

Do not duplicate `conversation_id` in both the URL and request body.

---

# 7. `schemas/conversation.py`

Create:

```text
src/chatterlite/schemas/conversation.py
```

```python
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
```

## Why `direct_key` is not exposed

`direct_key` is an internal database implementation detail.

The frontend does not need this:

```json
{
  "direct_key": "uuid-a:uuid-b"
}
```

The frontend only needs the conversation ID and its visible data.

Do not expose internal fields merely because they exist in the database.

---

# 8. `schemas/notification.py`

Create:

```text
src/chatterlite/schemas/notification.py
```

```python
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
```

Notification creation is usually internal business logic.

You do not need a public schema such as:

```python
NotificationCreate
```

because the frontend should not be allowed to create arbitrary notifications.

The backend creates notifications when an event occurs.

---

# 9. `schemas/__init__.py`

Create:

```text
src/chatterlite/schemas/__init__.py
```

```python
from chatterlite.schemas.common import (
    CursorPage,
    ErrorDetail,
    ErrorResponse,
    PaginationQuery,
)
from chatterlite.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    ConversationUpdate,
    DirectConversationCreate,
    GroupConversationCreate,
)
from chatterlite.schemas.member import (
    AddConversationMembersRequest,
    ConversationMemberResponse,
    UpdateMemberRoleRequest,
)
from chatterlite.schemas.message import (
    MarkConversationReadRequest,
    MessageCreate,
    MessageListResponse,
    MessagePreview,
    MessageResponse,
)
from chatterlite.schemas.notification import (
    NotificationListResponse,
    NotificationReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from chatterlite.schemas.user import (
    UserCreate,
    UserResponse,
    UserSearchResponse,
    UserSummary,
    UserUpdate,
)


__all__ = [
    "CursorPage",
    "ErrorDetail",
    "ErrorResponse",
    "PaginationQuery",
    "UserCreate",
    "UserUpdate",
    "UserSummary",
    "UserResponse",
    "UserSearchResponse",
    "DirectConversationCreate",
    "GroupConversationCreate",
    "ConversationUpdate",
    "ConversationSummary",
    "ConversationResponse",
    "ConversationListResponse",
    "AddConversationMembersRequest",
    "UpdateMemberRoleRequest",
    "ConversationMemberResponse",
    "MessageCreate",
    "MarkConversationReadRequest",
    "MessagePreview",
    "MessageResponse",
    "MessageListResponse",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationUnreadCountResponse",
    "NotificationReadResponse",
]
```

Importing from the package becomes cleaner:

```python
from chatterlite.schemas import (
    DirectConversationCreate,
    ConversationResponse,
)
```

Instead of:

```python
from chatterlite.schemas.conversation import (
    DirectConversationCreate,
    ConversationResponse,
)
```

Both work. The package export is just more convenient.

---

# 10. Example usage in a route

```python
from fastapi import APIRouter, status

from chatterlite.schemas import (
    DirectConversationCreate,
    ConversationResponse,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/direct",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_direct_conversation(
    payload: DirectConversationCreate,
) -> ConversationResponse:
    # Service implementation comes next.
    raise NotImplementedError
```

FastAPI uses the schema to:

```text
Validate request data
Generate Swagger documentation
Serialize the response
Reject invalid input
```

---

# 11. Request and response separation

Do not reuse one schema for everything.

Bad:

```python
class ConversationSchema(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    member_ids: list[UUID]
```

This mixes:

```text
Client input
Database-generated values
Nested output
Internal state
```

Better:

```text
GroupConversationCreate
ConversationUpdate
ConversationSummary
ConversationResponse
```

Each schema has one responsibility.

---

# 12. Schemas do not replace service validation

Pydantic can validate:

```text
Message is not empty
Message is under 4,000 characters
UUID has valid syntax
Group title has valid length
List is not empty
```

Pydantic cannot determine:

```text
Does the user exist?
Is the requester a conversation member?
Is the requester the group owner?
Does the message belong to this conversation?
Is the direct conversation already present?
Can this admin remove this member?
```

Those checks belong in services using PostgreSQL.

The rule is:

```text
Schema validation
→ Is the request structurally valid?

Service validation
→ Is the operation allowed and logically valid?
```

---

# 13. Important ORM loading rule

A response such as:

```python
class ConversationResponse(BaseModel):
    members: list[ConversationMemberResponse]
```

requires the SQLAlchemy relationship to be loaded before serialization.

Use eager loading later:

```python
select(Conversation).options(
    selectinload(
        Conversation.members
    ).selectinload(
        ConversationMember.user
    )
)
```

Do not return an ORM conversation with unloaded async relationships and expect Pydantic to magically query the database.

That commonly produces errors such as:

```text
MissingGreenlet
DetachedInstanceError
```

Routes and services must load the relationships required by the response schema.

---

# 14. Fields intentionally hidden from responses

Do not expose these merely because they exist:

```text
Conversation.direct_key
User internal authentication information
Database-only constraint values
Redis keys
Connection IDs
Internal error traces
```

API schemas represent the public contract—not a database dump.

---

# 15. Test schemas independently

You can test message validation:

```powershell
poetry run python
```

```python
from uuid import uuid4

from chatterlite.schemas.message import (
    MessageCreate,
)


message = MessageCreate(
    client_message_id=uuid4(),
    content="   Hello ChatterLite   ",
)

print(message)
```

Expected cleaned content:

```text
Hello ChatterLite
```

Test invalid content:

```python
MessageCreate(
    client_message_id=uuid4(),
    content="     ",
)
```

Expected:

```text
ValidationError:
Message content cannot be empty.
```

---

# 16. Current schema completion checklist

```text
✅ Common error schemas
✅ Cursor pagination structure
✅ User create/update/response schemas
✅ User summary schema
✅ Conversation creation schemas
✅ Conversation update schema
✅ Conversation summary and detail schemas
✅ Member management schemas
✅ Message creation schema
✅ Message response and pagination schemas
✅ Read-state request schema
✅ Notification response schemas
✅ Pydantic ORM conversion configured
✅ Internal fields hidden
✅ Validation separated from permissions
```

---

# 17. What comes after schemas

Once these schemas exist, move into:

```text
Phase 3 — Conversation REST API
```

Implementation order:

```text
1. Authentication dependency
2. User search
3. Create or return direct conversation
4. Create group conversation
5. List conversations
6. Load one conversation
7. List conversation members
8. Add group members
9. Remove group members
10. Update member roles
11. Leave group
```

Do not begin WebSockets yet.

First make conversations and messages work correctly through REST. Then realtime becomes a delivery layer instead of a debugging nightmare. 🔧
