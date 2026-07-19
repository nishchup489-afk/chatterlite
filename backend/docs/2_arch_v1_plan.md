# ChatterLite Backend Architecture

## 1. Product scope

ChatterLite supports:

1. **One-to-one messaging**
2. **Group conversations**
3. **In-app notifications**
4. **Online/offline presence and last seen**

Not included in the MVP:

* Voice or video calls
* File uploads
* Message reactions
* Typing indicators
* End-to-end encryption
* Email or mobile push notifications
* Message search
* Microservices
* Kafka, RabbitMQ, or Celery

Build a **modular monolith**. One clean FastAPI application is the right architecture.

---

# 2. Technology stack

```text
Frontend         Next.js
Authentication   Clerk
Backend          FastAPI
ORM              SQLAlchemy 2 async
Database         PostgreSQL
Cache/realtime   Redis
Realtime         WebSockets
Validation       Pydantic
Migrations       Alembic
Package manager  Poetry
Deployment       One FastAPI service
```

## Responsibility boundaries

```text
PostgreSQL
├── Users
├── Conversations
├── Members
├── Messages
├── Notifications
└── Last-seen timestamps

Redis
├── Active WebSocket connections
├── Online/offline presence
├── Presence heartbeats
├── Cross-server event delivery
└── Rate limiting

WebSocket
├── Send and receive messages
├── Receive notifications
├── Read-state updates
└── Presence updates

REST API
├── Initial data loading
├── Conversation management
├── Message history
├── Group management
└── Notification history
```

The central rule:

> PostgreSQL stores permanent truth. Redis stores temporary live state. WebSockets deliver live events.

---

# 3. High-level system architecture

```text
┌─────────────────────────────┐
│       Next.js Client        │
│                             │
│ Clerk session               │
│ REST requests               │
│ WebSocket connection        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│             FastAPI Backend             │
│                                         │
│ Auth module                             │
│ Conversation service                    │
│ Message service                         │
│ Notification service                    │
│ Presence service                        │
│ WebSocket manager                       │
│ Redis event listener                    │
└──────────────┬──────────────┬───────────┘
               │              │
               ▼              ▼
      ┌────────────────┐   ┌────────────────┐
      │   PostgreSQL   │   │     Redis      │
      │                │   │                │
      │ Persistent     │   │ Presence       │
      │ application    │   │ Heartbeats     │
      │ data           │   │ Pub/Sub        │
      └────────────────┘   └────────────────┘
```

---

# 4. Core architectural decision

Do not create separate direct-message and group-message systems.

Both use the same model:

```text
Conversation
├── type: DIRECT or GROUP
├── members
└── messages
```

A direct conversation has exactly two active members.

A group conversation has two or more members and supports roles.

This avoids duplicate code such as:

```text
direct_messages
group_messages
direct_message_service
group_message_service
```

You need only:

```text
conversations
conversation_members
messages
```

---

# 5. Database schema

## 5.1 Users

```text
users
├── id UUID primary key
├── clerk_user_id VARCHAR unique not null
├── username VARCHAR unique not null
├── display_name VARCHAR not null
├── avatar_url VARCHAR nullable
├── last_seen_at TIMESTAMPTZ nullable
├── created_at TIMESTAMPTZ not null
└── updated_at TIMESTAMPTZ not null
```

### Important rule

Do not add this to PostgreSQL:

```text
is_online BOOLEAN
```

Online status is temporary and can become stale when:

* A browser crashes
* Wi-Fi disconnects
* A server restarts
* A computer sleeps
* A WebSocket closes unexpectedly

Current presence belongs in Redis.

`last_seen_at` belongs in PostgreSQL because it is persistent history.

---

## 5.2 Conversations

```text
conversations
├── id UUID primary key
├── type ENUM(DIRECT, GROUP) not null
├── title VARCHAR nullable
├── image_url VARCHAR nullable
├── direct_key VARCHAR nullable
├── created_by UUID references users.id
├── last_message_id UUID nullable
├── created_at TIMESTAMPTZ not null
└── updated_at TIMESTAMPTZ not null
```

### Direct conversation key

To prevent duplicate direct conversations, generate a deterministic key from the two user IDs:

```python
direct_key = ":".join(sorted([str(user_a_id), str(user_b_id)]))
```

Example:

```text
018f-user-a:018f-user-b
```

Database constraint:

```text
UNIQUE(direct_key)
```

For group conversations:

```text
direct_key = NULL
```

Recommended database rule:

```text
DIRECT conversation → direct_key required
GROUP conversation  → direct_key must be NULL
```

---

## 5.3 Conversation members

```text
conversation_members
├── id UUID primary key
├── conversation_id UUID references conversations.id
├── user_id UUID references users.id
├── role ENUM(OWNER, ADMIN, MEMBER) not null
├── last_read_message_id UUID nullable
├── last_read_at TIMESTAMPTZ nullable
├── is_muted BOOLEAN default false
├── joined_at TIMESTAMPTZ not null
└── left_at TIMESTAMPTZ nullable
```

Required constraint:

```text
UNIQUE(conversation_id, user_id)
```

### Why read state belongs here

Do not add:

```text
messages.is_read
```

A group message may be:

* Read by User A
* Unread by User B
* Read by User C

Read state belongs to the relationship between a user and a conversation.

Therefore:

```text
conversation_members.last_read_message_id
```

is the correct MVP design.

---

## 5.4 Messages

```text
messages
├── id UUID primary key
├── conversation_id UUID references conversations.id
├── sender_id UUID references users.id
├── client_message_id UUID not null
├── message_type ENUM(TEXT, SYSTEM) default TEXT
├── content TEXT nullable
├── reply_to_message_id UUID nullable
├── created_at TIMESTAMPTZ not null
├── edited_at TIMESTAMPTZ nullable
└── deleted_at TIMESTAMPTZ nullable
```

Required constraint:

```text
UNIQUE(sender_id, client_message_id)
```

This makes message creation idempotent.

If the frontend retries the same message because of a connection problem, the backend returns the original message instead of inserting a duplicate.

### Important indexes

```text
INDEX messages(conversation_id, created_at DESC, id DESC)
INDEX messages(sender_id, created_at DESC)
INDEX messages(reply_to_message_id)
```

Use `created_at + id` for stable cursor pagination.

---

## 5.5 Notifications

```text
notifications
├── id UUID primary key
├── recipient_id UUID references users.id
├── actor_id UUID references users.id nullable
├── type ENUM(
│     NEW_MESSAGE,
│     ADDED_TO_GROUP,
│     REMOVED_FROM_GROUP,
│     PROMOTED_TO_ADMIN
│   )
├── conversation_id UUID nullable
├── message_id UUID nullable
├── title VARCHAR not null
├── body VARCHAR not null
├── is_read BOOLEAN default false
├── created_at TIMESTAMPTZ not null
└── read_at TIMESTAMPTZ nullable
```

Indexes:

```text
INDEX notifications(recipient_id, is_read, created_at DESC)
INDEX notifications(recipient_id, created_at DESC)
```

Notifications are persistent. Being offline must not cause a user to lose them.

---

# 6. Model relationships

```text
User
├── created conversations
├── conversation memberships
├── sent messages
├── received notifications
└── acted notifications

Conversation
├── members
├── messages
├── creator
└── last message

ConversationMember
├── user
├── conversation
└── last-read message

Message
├── conversation
├── sender
└── optional replied-to message

Notification
├── recipient
├── optional actor
├── optional conversation
└── optional message
```

---

# 7. Recommended project structure

```text
backend/
├── pyproject.toml
├── poetry.lock
├── alembic.ini
├── .env
├── .env.example
│
├── src/
│   └── chatterlite_backend/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── redis.py
│       │   ├── security.py
│       │   ├── logging.py
│       │   └── exceptions.py
│       │
│       ├── models/
│       │   ├── base.py
│       │   ├── enums.py
│       │   ├── user.py
│       │   ├── conversation.py
│       │   ├── conversation_member.py
│       │   ├── message.py
│       │   └── notification.py
│       │
│       ├── schemas/
│       │   ├── common.py
│       │   ├── user.py
│       │   ├── conversation.py
│       │   ├── member.py
│       │   ├── message.py
│       │   ├── notification.py
│       │   ├── presence.py
│       │   └── websocket.py
│       │
│       ├── api/
│       │   ├── router.py
│       │   ├── dependencies.py
│       │   └── routes/
│       │       ├── users.py
│       │       ├── conversations.py
│       │       ├── messages.py
│       │       ├── notifications.py
│       │       ├── presence.py
│       │       └── websocket.py
│       │
│       ├── services/
│       │   ├── user_service.py
│       │   ├── conversation_service.py
│       │   ├── message_service.py
│       │   ├── notification_service.py
│       │   ├── presence_service.py
│       │   └── realtime_service.py
│       │
│       ├── realtime/
│       │   ├── manager.py
│       │   ├── events.py
│       │   ├── redis_listener.py
│       │   └── presence_sweeper.py
│       │
│       └── db/
│           └── migrations/
│
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── websocket/
```

## Request flow

```text
Route
→ Pydantic validation
→ Service
→ SQLAlchemy / Redis
→ Response
```

Do not add a repository layer yet.

For this project:

```text
Route → Service → Database
```

is clean enough.

---

# 8. Service responsibilities

## UserService

Handles:

* Creating or synchronizing local Clerk users
* Finding users
* Searching usernames
* Loading basic profiles

## ConversationService

Handles:

* Creating or returning a direct conversation
* Creating groups
* Listing conversations
* Checking membership
* Adding members
* Removing members
* Changing member roles
* Leaving groups
* Updating group title or image

## MessageService

Handles:

* Validating message content
* Checking conversation membership
* Creating idempotent messages
* Updating conversation last message
* Loading message history
* Marking a conversation as read

## NotificationService

Handles:

* Creating notifications
* Listing notifications
* Calculating unread count
* Marking one notification as read
* Marking all notifications as read

## PresenceService

Handles:

* Registering live connections
* Refreshing heartbeat TTLs
* Removing connections
* Checking whether users are online
* Returning presence snapshots
* Detecting online/offline transitions
* Updating `last_seen_at`

## RealtimeService

Handles:

* Publishing Redis events
* Targeting users
* Building WebSocket payloads
* Delivering cross-server events

## WebSocketManager

Handles only local socket connections:

```python
connections: dict[UUID, dict[str, WebSocket]]
```

It should support:

```python
connect(user_id, connection_id, websocket)
disconnect(user_id, connection_id)
send_to_connection(connection_id, event)
send_to_user(user_id, event)
send_to_users(user_ids, event)
```

Do not put SQL queries or business logic inside the WebSocket manager.

---

# 9. REST API architecture

Base path:

```text
/api/v1
```

## Users

```http
GET /api/v1/users/search?q=nish
GET /api/v1/users/{user_id}
```

---

## Conversations

### Create or return a direct conversation

```http
POST /api/v1/conversations/direct
```

Request:

```json
{
  "user_id": "other-user-uuid"
}
```

Backend flow:

```text
Authenticated user
→ reject self-conversation
→ sort both user IDs
→ generate direct_key
→ find existing conversation
→ return existing or create new
```

### Create a group

```http
POST /api/v1/conversations/groups
```

Request:

```json
{
  "title": "Backend Warriors",
  "member_ids": [
    "user-uuid-1",
    "user-uuid-2"
  ]
}
```

The authenticated creator automatically becomes `OWNER`.

### List conversations

```http
GET /api/v1/conversations?limit=20&cursor=...
```

Each conversation response should include:

```json
{
  "id": "conversation-uuid",
  "type": "group",
  "title": "Backend Warriors",
  "image_url": null,
  "members": [],
  "last_message": {},
  "unread_count": 3,
  "updated_at": "2026-07-18T23:00:00Z"
}
```

Sort by:

```text
conversations.updated_at DESC
```

### Get one conversation

```http
GET /api/v1/conversations/{conversation_id}
```

### Update group

```http
PATCH /api/v1/conversations/{conversation_id}
```

Only group owners or admins may update group metadata.

---

## Group members

```http
GET    /api/v1/conversations/{conversation_id}/members
POST   /api/v1/conversations/{conversation_id}/members
PATCH  /api/v1/conversations/{conversation_id}/members/{user_id}
DELETE /api/v1/conversations/{conversation_id}/members/{user_id}
POST   /api/v1/conversations/{conversation_id}/leave
```

Direct conversation membership cannot be edited.

---

## Messages

### Load message history

```http
GET /api/v1/conversations/{conversation_id}/messages
```

Query:

```text
?limit=30&before_created_at=...&before_id=...
```

Use cursor pagination.

Do not use:

```text
?page=1000
```

### Optional REST fallback for sending

```http
POST /api/v1/conversations/{conversation_id}/messages
```

WebSocket can be the primary send mechanism, but a REST fallback makes testing and recovery easier.

### Mark conversation read

```http
POST /api/v1/conversations/{conversation_id}/read
```

Request:

```json
{
  "message_id": "latest-visible-message-uuid"
}
```

---

## Notifications

```http
GET  /api/v1/notifications
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/{notification_id}/read
POST /api/v1/notifications/read-all
```

---

## Presence

Initial presence snapshot:

```http
POST /api/v1/presence/snapshot
```

Request:

```json
{
  "user_ids": [
    "user-1",
    "user-2"
  ]
}
```

Response:

```json
{
  "users": [
    {
      "user_id": "user-1",
      "status": "online",
      "last_seen_at": null
    },
    {
      "user_id": "user-2",
      "status": "offline",
      "last_seen_at": "2026-07-18T20:00:00Z"
    }
  ]
}
```

The backend must verify that the requester shares a conversation with the requested users.

---

# 10. WebSocket architecture

Endpoint:

```text
/api/v1/ws
```

Use one socket per browser tab or device.

A user can have multiple active connections:

```text
User
├── Laptop tab 1
├── Laptop tab 2
└── Phone
```

The user is online while at least one valid connection remains.

---

# 11. WebSocket authentication

The client obtains a short-lived Clerk token and connects:

```text
wss://api.example.com/api/v1/ws?token=<session-token>
```

Backend connection flow:

```text
Accept connection attempt
→ validate Clerk token
→ extract clerk_user_id
→ load local user
→ generate connection_id
→ register socket
→ register Redis presence
```

Never trust identity data sent in the event body.

Bad:

```json
{
  "sender_id": "user-controlled-id"
}
```

The sender must always come from the verified authentication token.

---

# 12. WebSocket event envelope

Use the same structure for every event.

```json
{
  "event": "message.send",
  "request_id": "request-uuid",
  "data": {}
}
```

Server error:

```json
{
  "event": "error",
  "request_id": "request-uuid",
  "error": {
    "code": "NOT_CONVERSATION_MEMBER",
    "message": "You are not a member of this conversation."
  }
}
```

Use stable machine-readable error codes.

---

# 13. Client-to-server WebSocket events

## Send message

```json
{
  "event": "message.send",
  "request_id": "request-uuid",
  "data": {
    "client_message_id": "client-generated-uuid",
    "conversation_id": "conversation-uuid",
    "content": "Hello"
  }
}
```

## Mark conversation read

```json
{
  "event": "message.read",
  "request_id": "request-uuid",
  "data": {
    "conversation_id": "conversation-uuid",
    "message_id": "message-uuid"
  }
}
```

## Presence heartbeat

```json
{
  "event": "presence.heartbeat",
  "request_id": "request-uuid",
  "data": {}
}
```

Recommended interval:

```text
Client heartbeat: 20 seconds
Redis TTL:        60 seconds
```

## Request presence snapshot

```json
{
  "event": "presence.get",
  "request_id": "request-uuid",
  "data": {
    "user_ids": [
      "user-1",
      "user-2"
    ]
  }
}
```

---

# 14. Server-to-client WebSocket events

## Message acknowledgment

```json
{
  "event": "message.ack",
  "request_id": "original-request-uuid",
  "data": {
    "client_message_id": "client-generated-uuid",
    "message_id": "database-message-uuid",
    "status": "created"
  }
}
```

If the message was a retry:

```json
{
  "status": "already_exists"
}
```

## Message created

```json
{
  "event": "message.created",
  "data": {
    "id": "message-uuid",
    "conversation_id": "conversation-uuid",
    "sender": {
      "id": "user-uuid",
      "display_name": "Nishchup",
      "avatar_url": null
    },
    "content": "Hello",
    "created_at": "2026-07-18T23:00:00Z"
  }
}
```

## Message read

```json
{
  "event": "message.read",
  "data": {
    "conversation_id": "conversation-uuid",
    "user_id": "reader-user-uuid",
    "message_id": "message-uuid",
    "read_at": "2026-07-18T23:01:00Z"
  }
}
```

## Notification created

```json
{
  "event": "notification.created",
  "data": {
    "id": "notification-uuid",
    "type": "new_message",
    "conversation_id": "conversation-uuid",
    "message_id": "message-uuid",
    "title": "New message",
    "body": "Nishchup sent you a message"
  }
}
```

## Presence online

```json
{
  "event": "presence.online",
  "data": {
    "user_id": "user-uuid",
    "status": "online"
  }
}
```

## Presence offline

```json
{
  "event": "presence.offline",
  "data": {
    "user_id": "user-uuid",
    "status": "offline",
    "last_seen_at": "2026-07-18T23:40:00Z"
  }
}
```

## Presence snapshot

```json
{
  "event": "presence.snapshot",
  "request_id": "request-uuid",
  "data": {
    "users": [
      {
        "user_id": "user-1",
        "status": "online",
        "last_seen_at": null
      },
      {
        "user_id": "user-2",
        "status": "offline",
        "last_seen_at": "2026-07-18T22:10:00Z"
      }
    ]
  }
}
```

---

# 15. Message sending pipeline

This is the central backend flow.

```text
Client sends message.send
        │
        ▼
WebSocket route validates event structure
        │
        ▼
MessageService:
├── validate authenticated user
├── validate conversation exists
├── verify active membership
├── validate content
└── check client_message_id
        │
        ▼
PostgreSQL transaction:
├── insert message
├── update conversation.last_message_id
├── update conversation.updated_at
└── create recipient notifications
        │
        ▼
Commit transaction
        │
        ▼
Send message.ack to sender
        │
        ▼
Publish message.created through Redis
        │
        ▼
Every backend instance receives event
        │
        ▼
Instances deliver event to connected recipients
```

Never publish the realtime event before the database transaction commits.

Otherwise, a client could receive a message that does not exist in PostgreSQL.

---

# 16. Offline message behavior

A recipient does not need to be online when a message is sent.

```text
Message sent
→ message stored in PostgreSQL
→ notification stored in PostgreSQL
→ realtime event attempted
```

If the recipient is offline:

```text
No WebSocket delivery occurs
```

When the recipient reconnects:

```text
GET conversations
GET unread notifications
GET unread messages
```

PostgreSQL ensures nothing is lost.

WebSocket delivery is an optimization, not the source of truth.

---

# 17. Notification rules

For every new message:

```text
Recipients =
all active conversation members
except the sender
```

For a direct conversation:

```text
one recipient
```

For a group:

```text
all other active members
```

For each recipient:

1. Create a PostgreSQL notification.
2. Publish `notification.created`.
3. Update the frontend unread badge when connected.

A connected user is not automatically considered to have read the message.

They may be online but looking at another conversation.

---

# 18. Presence system

## Presence rules

A user is online when:

```text
At least one valid WebSocket connection exists
```

A user becomes offline when:

```text
All of their connection records have disappeared or expired
```

Closing one tab must not mark the user offline if another tab or phone is still connected.

---

# 19. Redis presence keys

## Connection key

```text
presence:connection:{connection_id}
```

Value:

```json
{
  "user_id": "user-uuid",
  "instance_id": "backend-instance-id"
}
```

TTL:

```text
60 seconds
```

## User connection set

```text
presence:user:{user_id}:connections
```

Members:

```text
connection-id-1
connection-id-2
connection-id-3
```

## Presence expiration queue

Use a Redis sorted set:

```text
presence:expirations
```

Member:

```text
user_id|connection_id
```

Score:

```text
expiration Unix timestamp
```

This allows the presence sweeper to find expired connections without scanning every Redis key.

---

# 20. Presence lifecycle

## On first connection

```text
1. Generate connection_id
2. Register local WebSocket
3. Set connection key with 60-second TTL
4. Add connection_id to user connection set
5. Add expiration entry to sorted set
6. Check whether user was previously offline
7. If yes, publish presence.online
```

## On heartbeat

```text
1. Refresh connection key TTL
2. Update sorted-set expiration score
3. Optionally respond with heartbeat acknowledgment
```

## On clean disconnect

```text
1. Remove local WebSocket
2. Delete connection key
3. Remove connection ID from user set
4. Remove expiration entry
5. Check for other valid connections
6. If none remain:
   - update users.last_seen_at
   - publish presence.offline
```

## On unclean disconnect

Examples:

* Browser crash
* Internet loss
* Computer shutdown
* Backend instance crash

Flow:

```text
Heartbeat stops
→ connection TTL expires
→ presence sweeper finds expiration
→ stale connection is removed
→ if no valid connections remain:
   user transitions offline
```

---

# 21. Presence sweeper

Run a lightweight background loop every 15–30 seconds.

```text
Read expired entries from presence:expirations
→ remove stale connection IDs
→ check remaining live connections
→ transition affected users offline
```

Pseudo-flow:

```python
while application_is_running:
    expired_connections = get_expired_connections()

    for user_id, connection_id in expired_connections:
        remove_stale_connection(user_id, connection_id)

        if not user_has_live_connections(user_id):
            update_last_seen(user_id)
            publish_presence_offline(user_id)

    await asyncio.sleep(15)
```

For multiple FastAPI instances, use a short Redis lock so only one instance performs the sweep at a time.

---

# 22. Presence subscribers

Do not broadcast every presence change to every ChatterLite user.

A user may receive another user’s presence only when they share at least one active conversation.

```text
Presence subscribers =
users sharing a conversation with the affected user
```

Before returning presence information, verify this relationship.

This prevents ChatterLite from becoming a global user-tracking endpoint.

---

# 23. Redis realtime Pub/Sub

Use one channel:

```text
chatterlite:realtime
```

Published event:

```json
{
  "event": "message.created",
  "target_user_ids": [
    "user-1",
    "user-2"
  ],
  "data": {}
}
```

Every FastAPI instance subscribes to the channel.

```text
Server 1 publishes event
→ Redis distributes event
→ Server 2 receives event
→ Server 2 checks local connections
→ Server 2 delivers to connected target users
```

This solves the multi-server problem:

```text
Sender connected to Server 1
Recipient connected to Server 2
```

Without Redis, Server 1 cannot reach Server 2’s sockets.

---

# 24. Group permission model

## Owner

Can:

* Rename group
* Change group image
* Add members
* Remove members
* Promote members
* Demote admins
* Transfer ownership
* Delete or close group later

Cannot accidentally remove themselves while still owner.

## Admin

Can:

* Add members
* Remove regular members
* Update group metadata

Cannot:

* Remove owner
* Promote someone to owner
* Demote owner

## Member

Can:

* Send messages
* Read messages
* Leave group

Cannot:

* Add or remove members
* Change roles
* Update group metadata

## Direct conversations

Roles are effectively regular members.

Membership cannot be manually added or removed.

---

# 25. Security requirements

Every conversation operation must verify membership.

Check membership before:

* Loading a conversation
* Loading messages
* Sending messages
* Marking messages read
* Viewing members
* Querying presence
* Adding or removing members

Other requirements:

```text
Maximum message length        4,000 characters
Group member limit            e.g. 100 for MVP
WebSocket payload size limit
Message rate limiting
Presence request size limit
User search rate limiting
Strict Pydantic validation
HTML escaping on frontend
```

Do not render raw messages with unsafe HTML.

---

# 26. Transaction boundaries

The following operations should happen in one PostgreSQL transaction:

```text
Create message
Update conversation
Create notifications
```

Group creation transaction:

```text
Create conversation
Create owner membership
Create member memberships
Create group notifications
```

Adding a member transaction:

```text
Create membership
Create notification
Create optional system message
```

Commit first, then publish realtime events.

---

# 27. Error codes

Use predictable application errors:

```text
UNAUTHORIZED
USER_NOT_FOUND
CONVERSATION_NOT_FOUND
NOT_CONVERSATION_MEMBER
DIRECT_CONVERSATION_EXISTS
INVALID_CONVERSATION_TYPE
MESSAGE_TOO_LONG
DUPLICATE_MESSAGE
GROUP_PERMISSION_DENIED
MEMBER_ALREADY_EXISTS
CANNOT_REMOVE_OWNER
INVALID_READ_MESSAGE
RATE_LIMITED
INVALID_WEBSOCKET_EVENT
```

Do not return vague messages such as:

```text
Something went wrong
```

Return a safe human-readable message plus a stable code.

---

# 28. Application lifecycle

## Startup

```text
1. Load configuration
2. Initialize PostgreSQL engine
3. Verify database connectivity
4. Initialize Redis client
5. Verify Redis connectivity
6. Start Redis Pub/Sub listener
7. Start presence sweeper
8. Accept traffic
```

## Shutdown

```text
1. Stop accepting new WebSockets
2. Close active local sockets
3. Stop Redis listener
4. Stop presence sweeper
5. Close Redis connection
6. Dispose database engine
```

---

# 29. Configuration

Example environment variables:

```env
APP_ENV=development
APP_NAME=ChatterLite

DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...

CLERK_SECRET_KEY=...
CLERK_JWKS_URL=...

CORS_ORIGINS=http://localhost:3000

PRESENCE_TTL_SECONDS=60
PRESENCE_HEARTBEAT_SECONDS=20
PRESENCE_SWEEP_SECONDS=15

MESSAGE_MAX_LENGTH=4000
GROUP_MAX_MEMBERS=100
```

Never commit `.env`.

Commit `.env.example` without secrets.

---

# 30. Testing architecture

## Unit tests

Test services independently:

* Direct-key generation
* Permission checks
* Message validation
* Notification recipient calculation
* Presence transition logic
* Cursor creation and parsing

## Integration tests

Test with PostgreSQL and Redis:

* Create direct conversation
* Prevent duplicate direct conversations
* Create group
* Add and remove group members
* Reject unauthorized message access
* Store messages
* Create notifications
* Update last-read state
* Update last seen

## WebSocket tests

Test:

* Valid authentication
* Invalid authentication
* Sending a message
* Receiving acknowledgment
* Receiving message events
* Duplicate message retry
* Multiple browser tabs
* Heartbeat refresh
* Online transition
* Offline transition
* Abrupt socket loss

## Multi-instance tests

Run two backend instances and verify:

```text
User A → backend instance 1
User B → backend instance 2
```

Then test:

* Message delivery
* Notification delivery
* Presence updates
* Disconnect behavior

---

