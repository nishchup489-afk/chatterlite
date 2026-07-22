# Phase 2 — Database Models

Your goal in this phase is simple:

> Build the permanent PostgreSQL structure for users, direct chats, group chats, messages, notifications, and last-seen history.

Redis and WebSockets come later. Phase 2 is **database only**.

Your agreed database design uses one shared `Conversation` system for both direct and group chats. 

---

## Phase 2 checklist

```text
1. Create database enums
2. Create User model
3. Create Conversation model
4. Create ConversationMember model
5. Create Message model
6. Create Notification model
7. Add relationships
8. Add constraints and indexes
9. Configure Alembic
10. Generate and run migration
11. Verify tables in PostgreSQL
```

---

# 1. Models folder

```text
src/
└── chatterlite_backend/
    └── models/
        ├── __init__.py
        ├── base.py
        ├── enums.py
        ├── user.py
        ├── conversation.py
        ├── conversation_member.py
        ├── message.py
        └── notification.py
```

Do not put every model inside one giant `models.py`.

At the same time, do not create unnecessary folders like:

```text
models/user/
models/message/
models/conversation/
```

One file per model is enough for this project.

---

# 2. Database enums

Create these enums first.

## Conversation type

```python
class ConversationType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
```

## Member role

```python
class MemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
```

## Message type

```python
class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
```

## Notification type

```python
class NotificationType(str, Enum):
    NEW_MESSAGE = "new_message"
    ADDED_TO_GROUP = "added_to_group"
    REMOVED_FROM_GROUP = "removed_from_group"
    PROMOTED_TO_ADMIN = "promoted_to_admin"
```

For the MVP, these are enough.

---

# 3. User model

```text
users
├── id
├── clerk_user_id
├── username
├── display_name
├── avatar_url
├── last_seen_at
├── created_at
└── updated_at
```

## Important decisions

### `clerk_user_id`

This connects your PostgreSQL user to Clerk.

```text
clerk_user_id = user_2abc123...
```

It must be:

```text
unique
not null
indexed
```

### `last_seen_at`

This stores the last known offline time.

```text
2026-07-21 14:30:00+00
```

Do not add:

```python
is_online = Column(Boolean)
```

Online status belongs in Redis because it is temporary.

---

# 4. Conversation model

Both direct and group chats use this model.

```text
conversations
├── id
├── type
├── title
├── image_url
├── direct_key
├── created_by
├── last_message_id
├── created_at
└── updated_at
```

## Direct conversation

```text
type = DIRECT
title = null
direct_key = user_a:user_b
```

## Group conversation

```text
type = GROUP
title = Backend Warriors
direct_key = null
```

---

## Why `direct_key` exists

Without it, Alice and Bob could accidentally create multiple direct conversations:

```text
Conversation 1: Alice ↔ Bob
Conversation 2: Alice ↔ Bob
Conversation 3: Alice ↔ Bob
```

Generate the key by sorting both UUIDs:

```python
def create_direct_key(
    first_user_id: UUID,
    second_user_id: UUID,
) -> str:
    return ":".join(
        sorted(
            [
                str(first_user_id),
                str(second_user_id),
            ]
        )
    )
```

Database rule:

```text
UNIQUE(direct_key)
```

PostgreSQL allows multiple `NULL` values in a unique column, so group conversations can all have:

```text
direct_key = NULL
```

---

# 5. ConversationMember model

This model connects users and conversations.

```text
conversation_members
├── id
├── conversation_id
├── user_id
├── role
├── last_read_message_id
├── last_read_at
├── is_muted
├── joined_at
└── left_at
```

Required constraint:

```text
UNIQUE(conversation_id, user_id)
```

This prevents the same user from being added twice.

---

## Direct conversation members

A direct conversation has exactly two memberships:

```text
Alice → conversation 123
Bob   → conversation 123
```

Both can use:

```text
role = MEMBER
```

---

## Group conversation members

```text
Creator → OWNER
Admin   → ADMIN
Others  → MEMBER
```

---

## Why read state belongs here

Do not put this on `Message`:

```python
is_read = Column(Boolean)
```

That fails for groups.

Suppose three people receive one message:

```text
Alice: read
Bob: unread
Charlie: read
```

One Boolean cannot represent all three states.

Instead, each membership stores:

```text
last_read_message_id
last_read_at
```

Anything newer than `last_read_message_id` is unread for that member.

---

# 6. Message model

```text
messages
├── id
├── conversation_id
├── sender_id
├── client_message_id
├── message_type
├── content
├── reply_to_message_id
├── created_at
├── edited_at
└── deleted_at
```

For now, you mainly use:

```text
id
conversation_id
sender_id
client_message_id
message_type
content
created_at
```

The other fields prepare you for basic editing, deletion, and replies without requiring a redesign.

---

## `client_message_id`

The frontend generates this UUID before sending:

```json
{
  "client_message_id": "343d91fa-...",
  "content": "Hello"
}
```

Required constraint:

```text
UNIQUE(sender_id, client_message_id)
```

Why?

The client may send a message and lose connection before receiving confirmation. It retries the same message.

Without idempotency:

```text
Hello
Hello
```

With `client_message_id`, the backend recognizes the retry and returns the existing message.

This is useful, but not complex magic. It is one UUID and one constraint.

---

## Message indexes

Add:

```text
INDEX(conversation_id, created_at DESC, id DESC)
INDEX(sender_id, created_at DESC)
INDEX(reply_to_message_id)
```

The first index is the important one because message history is loaded by conversation.

---

# 7. Notification model

```text
notifications
├── id
├── recipient_id
├── actor_id
├── type
├── conversation_id
├── message_id
├── title
├── body
├── is_read
├── created_at
└── read_at
```

Example:

```text
recipient_id    Bob
actor_id        Alice
type            NEW_MESSAGE
conversation_id Direct conversation
message_id      Message UUID
title           New message
body            Alice sent you a message
is_read         false
```

Notifications must be saved in PostgreSQL.

If Bob is offline, the notification still exists when he returns.

---

## Notification indexes

```text
INDEX(recipient_id, is_read, created_at DESC)
INDEX(recipient_id, created_at DESC)
```

These support:

```text
Load my latest notifications
Count my unread notifications
```

---

# 8. Relationships

## User

```text
User
├── created_conversations
├── conversation_memberships
├── sent_messages
├── received_notifications
└── actor_notifications
```

## Conversation

```text
Conversation
├── creator
├── members
├── messages
└── last_message
```

## ConversationMember

```text
ConversationMember
├── conversation
├── user
└── last_read_message
```

## Message

```text
Message
├── conversation
├── sender
└── reply_to_message
```

## Notification

```text
Notification
├── recipient
├── actor
├── conversation
└── message
```

---

# 9. Important constraints

You need these constraints:

```text
users.clerk_user_id UNIQUE
users.username UNIQUE

conversations.direct_key UNIQUE

conversation_members:
UNIQUE(conversation_id, user_id)

messages:
UNIQUE(sender_id, client_message_id)
```

You should also eventually enforce:

```text
DIRECT → direct_key is not null
GROUP  → direct_key is null
```

But this check constraint can wait until the core models work. Do not let one fancy constraint block the entire phase.

---

# 10. Model creation order

Create them in this order:

```text
1. Enums
2. User
3. Conversation
4. ConversationMember
5. Message
6. Notification
7. Relationships
```

There is one circular foreign-key situation:

```text
Conversation.last_message_id → Message.id
Message.conversation_id      → Conversation.id
```

That is normal.

But to reduce confusion while learning, you can initially leave out:

```text
Conversation.last_message_id
```

Then add it in a later migration after messages work.

Your simpler first database version can use:

```text
Conversation.updated_at
```

for sorting conversations.

That is the better learning move right now.

---

# 11. Simplified Phase 2 schema

For your first working migration, use this exact scope:

## User

```text
id
clerk_user_id
username
display_name
avatar_url
last_seen_at
created_at
updated_at
```

## Conversation

```text
id
type
title
image_url
direct_key
created_by
created_at
updated_at
```

## ConversationMember

```text
id
conversation_id
user_id
role
last_read_message_id
last_read_at
is_muted
joined_at
left_at
```

## Message

```text
id
conversation_id
sender_id
client_message_id
message_type
content
reply_to_message_id
created_at
edited_at
deleted_at
```

## Notification

```text
id
recipient_id
actor_id
type
conversation_id
message_id
title
body
is_read
created_at
read_at
```

---

# 12. Alembic steps

After all models are created and imported properly:

```bash
poetry run alembic revision --autogenerate -m "create initial chat models"
```

Review the generated migration.

Then run:

```bash
poetry run alembic upgrade head
```

Check current migration:

```bash
poetry run alembic current
```

Check migration history:

```bash
poetry run alembic history
```

---

# 13. Phase 2 completion criteria

Phase 2 is complete only when:

```text
✅ All five tables exist
✅ Foreign keys exist
✅ Unique constraints exist
✅ Important indexes exist
✅ Alembic migration runs successfully
✅ Alembic downgrade works
✅ PostgreSQL can create users
✅ Direct and group conversations can be represented
✅ Messages can be linked to conversations
✅ Notifications can be linked to recipients
```

Do not build WebSocket routes yet.

Do not build Redis presence yet.

Do not build message services yet.

The final Phase 2 deliverable is:

```text
A clean, migrated PostgreSQL schema that can support every MVP feature.
```
