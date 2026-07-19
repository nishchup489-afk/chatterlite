# 31. Recommended implementation order

## Phase 1 — Foundation

```text
FastAPI application
Configuration
Async PostgreSQL
Redis
Alembic
Logging
Error handling
Clerk authentication
```

## Phase 2 — Database models

```text
User
Conversation
ConversationMember
Message
Notification
Indexes
Constraints
Migrations
```

## Phase 3 — Conversation REST API

```text
User search
Create direct conversation
Create group
List conversations
Load one conversation
Group member management
```

## Phase 4 — Message history

```text
Create messages through REST first
Message validation
Cursor pagination
Last-message updates
Read state
```

Build REST message creation before WebSockets. This lets you verify the business logic without debugging two systems simultaneously.

## Phase 5 — WebSocket messaging

```text
WebSocket authentication
Connection manager
message.send
message.ack
message.created
message.read
```

## Phase 6 — Notifications

```text
Persistent notification creation
Notification listing
Unread count
Read endpoints
Realtime notification events
```

## Phase 7 — Presence

```text
Redis connection records
Heartbeat
Multiple tabs and devices
Online transition
Offline transition
Last seen
Presence sweeper
Presence events
```

## Phase 8 — Cross-server Redis delivery

```text
Redis Pub/Sub listener
Targeted user delivery
Multi-instance testing
```

## Phase 9 — Hardening

```text
Rate limiting
Structured logs
Better error reporting
Security tests
Load tests
Docker
Deployment
```

---

# 32. Final architecture map

```text
ChatterLite
│
├── Authentication
│   ├── Clerk token verification
│   └── Local PostgreSQL user
│
├── Conversation system
│   ├── Direct conversations
│   ├── Group conversations
│   ├── Members
│   └── Group roles
│
├── Message system
│   ├── PostgreSQL persistence
│   ├── Idempotent message sending
│   ├── Cursor pagination
│   ├── Read state
│   └── Realtime delivery
│
├── Notification system
│   ├── Persistent notifications
│   ├── Unread counts
│   ├── Read state
│   └── Realtime notification delivery
│
├── Presence system
│   ├── Redis connection records
│   ├── Heartbeats
│   ├── Multiple tabs and devices
│   ├── Online/offline transitions
│   ├── Presence sweeper
│   └── PostgreSQL last seen
│
├── Realtime system
│   ├── FastAPI WebSockets
│   ├── Local connection manager
│   ├── Redis Pub/Sub
│   └── Targeted event delivery
│
└── Infrastructure
    ├── PostgreSQL
    ├── Redis
    ├── Alembic
    ├── Poetry
    ├── Docker
    └── Structured logging
```

# Final source-of-truth rules

```text
Users              → PostgreSQL
Conversations      → PostgreSQL
Memberships        → PostgreSQL
Messages           → PostgreSQL
Notifications      → PostgreSQL
Last seen          → PostgreSQL

Current 
presence   → Redis
Heartbeats         → Redis
Connection records → Redis
Cross-server events→ Redis Pub/Sub

Initial data       → REST API
Historical data    → REST API
Live updates       → WebSocket
```

This architecture is large enough to be legitimate, but small enough for one developer to build and understand. It gives you real backend engineering practice without turning ChatterLite into a fake distributed-systems thesis.
