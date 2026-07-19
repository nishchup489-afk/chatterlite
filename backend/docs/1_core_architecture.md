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