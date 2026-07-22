# ChatterLite Database Models and Relationships

## 1. Purpose

ChatterLite uses five main database models:

```text
User
Conversation
ConversationMember
Message
Notification
```

Together, they support:

* One-to-one conversations
* Group conversations
* Sending and replying to messages
* Group roles and membership
* Read tracking
* Persistent notifications
* Last-seen timestamps

The central model flow is:

```text
User
  │
  ├── ConversationMember ── Conversation ── Message
  │
  └── Notification
```

In simple terms:

> Users join conversations through membership records, send messages inside those conversations, and receive notifications when something happens.

---

# 2. Database Connections vs ORM Relationships

SQLAlchemy connects models at two different levels.

## 2.1 `ForeignKey`

A foreign key creates the real database connection.

Example:

```python
sender_id = Column(UUID(as_uuid=True) , ForeignKey("users.id") , nullable=False)
```

This tells PostgreSQL:

> `messages.sender_id` must point to a valid row in `users.id`.

With only the foreign key, you can access:

```python
message.sender_id
```

But you only receive the sender’s UUID.

---

## 2.2 `relationship()`

A relationship creates a convenient Python-side connection.

```python
sender = relationship("User" , back_populates="sent_messages")
```

Now you can access the complete user object:

```python
message.sender
message.sender.username
message.sender.display_name
```

The relationship does not create another database column. It teaches SQLAlchemy how to navigate the existing foreign-key connection.

SQLAlchemy uses foreign-key constraints to determine how related tables join, while `relationship()` creates object-level attributes on the mapped Python classes.

---

# 3. `back_populates`

Most ChatterLite relationships work in both directions.

For example:

```python
class User:
    sent_messages = relationship("Message" , back_populates="sender")
```

```python
class Message:
    sender = relationship("User" , back_populates="sent_messages")
```

The names point at each other:

```text
User.sent_messages
        ↕
Message.sender
```

This allows both:

```python
user.sent_messages
```

and:

```python
message.sender
```

The value passed to `back_populates` must be the exact relationship attribute name on the other model.

SQLAlchemy uses `back_populates` to synchronize both sides of a bidirectional relationship and to understand how relationship changes should participate in persistence operations.

---

# 4. Complete Relationship Map

```text
User
├── created_conversations ─────────── Conversation.creator
├── memberships ───────────────────── ConversationMember.user
├── sent_messages ─────────────────── Message.sender
├── received_notifications ────────── Notification.recipient
└── acted_notifications ───────────── Notification.actor


Conversation
├── creator ───────────────────────── User.created_conversations
├── memberships ───────────────────── ConversationMember.conversation
├── messages ──────────────────────── Message.conversation
├── last_message ──────────────────── Message
└── notifications ─────────────────── Notification.conversation


ConversationMember
├── user ──────────────────────────── User.memberships
├── conversation ──────────────────── Conversation.memberships
└── last_read_message ─────────────── Message


Message
├── conversation ──────────────────── Conversation.messages
├── sender ────────────────────────── User.sent_messages
├── reply_to ──────────────────────── another Message
├── replies ───────────────────────── many Message objects
└── notifications ─────────────────── Notification.message


Notification
├── recipient ─────────────────────── User.received_notifications
├── actor ─────────────────────────── User.acted_notifications
├── conversation ──────────────────── Conversation.notifications
└── message ───────────────────────── Message.notifications
```

---

# 5. User Model

The `User` model represents one ChatterLite account.

```text
User
├── creates conversations
├── joins conversations
├── sends messages
├── receives notifications
└── causes notification events
```

## `created_conversations`

```python
created_conversations = relationship(
    "Conversation",
    back_populates="creator",
    foreign_keys="Conversation.created_by",
)
```

One user can create many conversations.

```text
User A
├── Direct conversation with User B
├── Group 1
└── Group 2
```

The corresponding database foreign key is:

```python
Conversation.created_by
```

Example usage:

```python
user.created_conversations
```

This returns a collection of conversations created by that user.

---

## `memberships`

```python
memberships = relationship(
    "ConversationMember",
    back_populates="user",
)
```

This returns all membership records belonging to the user.

Example:

```python
user.memberships
```

A membership is more than a simple connection. It stores:

```text
role
last-read message
mute status
join time
leave time
```

Therefore, ChatterLite does not directly model:

```text
User ↔ Conversation
```

It models:

```text
User ↔ ConversationMember ↔ Conversation
```

This is known as an association-object pattern: the middle model represents the connection while also storing information about that connection. SQLAlchemy documents this pattern for many-to-many relationships that require additional data on the association itself.

---

## `sent_messages`

```python
sent_messages = relationship(
    "Message",
    back_populates="sender",
    foreign_keys="Message.sender_id",
)
```

One user can send many messages.

```text
User A
├── Message 1
├── Message 2
└── Message 3
```

Example usage:

```python
user.sent_messages
```

---

## `received_notifications`

```python
received_notifications = relationship(
    "Notification",
    back_populates="recipient",
    foreign_keys="Notification.recipient_id",
)
```

This returns notifications sent to the user.

Example:

```python
user.received_notifications
```

---

## `acted_notifications`

```python
acted_notifications = relationship(
    "Notification",
    back_populates="actor",
    foreign_keys="Notification.actor_id",
)
```

This represents notifications caused by the user.

Example:

```text
Alice adds Bob to a group.
```

The notification contains:

```text
actor     = Alice
recipient = Bob
```

Therefore:

```python
alice.acted_notifications
bob.received_notifications
```

---

# 6. Conversation Model

The `Conversation` model is the container for messages.

It represents both:

```text
DIRECT conversation
GROUP conversation
```

## `creator`

```python
creator = relationship(
    "User",
    back_populates="created_conversations",
    foreign_keys=[created_by],
)
```

This returns the user who originally created the conversation.

```python
conversation.creator
```

For groups, this is usually the original owner.

For direct conversations, it is the user who first started the chat.

---

## `memberships`

```python
memberships = relationship(
    "ConversationMember",
    back_populates="conversation",
)
```

This returns the membership records inside the conversation.

```python
conversation.memberships
```

Each record tells you:

```text
which user belongs
their role
whether they muted the conversation
what message they last read
whether they have left
```

---

## `messages`

```python
messages = relationship(
    "Message",
    back_populates="conversation",
    foreign_keys="Message.conversation_id",
)
```

One conversation can contain many messages.

```text
Conversation
├── Message 1
├── Message 2
└── Message 3
```

Example:

```python
conversation.messages
```

The explicit `foreign_keys` argument is required because `Conversation` and `Message` have two different foreign-key paths:

```text
Message.conversation_id  → Conversation.id
Conversation.last_message_id → Message.id
```

Without guidance, SQLAlchemy may not know which path should be used for `Conversation.messages`. When multiple valid foreign-key routes exist, `foreign_keys` identifies the intended join path and prevents ambiguous-join errors.

---

## `last_message`

```python
last_message = relationship(
    "Message",
    foreign_keys=[last_message_id],
    post_update=True,
)
```

This points to one special message: the latest message in the conversation.

```python
conversation.last_message
```

This is useful for the conversation sidebar:

```text
Alice
"See you tomorrow"
5:30 PM
```

Instead of searching through every message to find the newest one, the conversation directly stores:

```text
last_message_id
```

---

## `notifications`

```python
notifications = relationship(
    "Notification",
    back_populates="conversation",
    foreign_keys="Notification.conversation_id",
)
```

This returns all notification records related to the conversation.

```python
conversation.notifications
```

---

# 7. ConversationMember Model

`ConversationMember` connects one user to one conversation.

```text
User
  ↓
ConversationMember
  ↓
Conversation
```

This model solves the many-to-many relationship:

```text
One user can join many conversations.
One conversation can contain many users.
```

## `user`

```python
user = relationship(
    "User",
    back_populates="memberships",
    foreign_keys=[user_id],
)
```

This returns the user represented by the membership.

```python
membership.user
```

---

## `conversation`

```python
conversation = relationship(
    "Conversation",
    back_populates="memberships",
    foreign_keys=[conversation_id],
)
```

This returns the conversation represented by the membership.

```python
membership.conversation
```

---

## `last_read_message`

```python
last_read_message = relationship(
    "Message",
    foreign_keys=[last_read_message_id],
)
```

This returns the newest message the user has read in this conversation.

```python
membership.last_read_message
```

This relationship does not need `back_populates` because ChatterLite does not need a reverse collection such as:

```python
message.members_who_read_until_this_message
```

That collection could become large and is unnecessary for the MVP.

---

# 8. Message Model

A `Message` belongs to one conversation and one sender.

It may also reply to another message.

## `conversation`

```python
conversation = relationship(
    "Conversation",
    back_populates="messages",
    foreign_keys=[conversation_id],
)
```

This returns the conversation containing the message.

```python
message.conversation
```

---

## `sender`

```python
sender = relationship(
    "User",
    back_populates="sent_messages",
    foreign_keys=[sender_id],
)
```

This returns the user who sent the message.

```python
message.sender
message.sender.username
```

The backend should determine `sender_id` from the authenticated Clerk identity rather than trusting a sender ID supplied by the frontend.

---

## `reply_to`

```python
reply_to = relationship(
    "Message",
    back_populates="replies",
    foreign_keys=[reply_to_message_id],
    remote_side=[id],
)
```

A message can point to another message.

```text
Message A: Are you coming?
Message B: Yes.
           ↳ replies to Message A
```

Then:

```python
message_b.reply_to
```

returns `Message A`.

---

## `replies`

```python
replies = relationship(
    "Message",
    back_populates="reply_to",
    foreign_keys=[reply_to_message_id],
)
```

This is the reverse direction.

```python
message_a.replies
```

returns all messages replying to Message A.

---

## Why `remote_side` is required

Both sides of the relationship use the same table:

```text
messages.reply_to_message_id → messages.id
```

SQLAlchemy therefore needs help distinguishing:

```text
Current message
Referenced message
```

```python
remote_side=[id]
```

tells SQLAlchemy that the referenced message’s `id` is the remote side of the relationship. This is the standard direction-setting mechanism for self-referential ORM relationships.

---

## `notifications`

```python
notifications = relationship(
    "Notification",
    back_populates="message",
    foreign_keys="Notification.message_id",
)
```

This returns notifications connected to the message.

```python
message.notifications
```

For example, one group message may create notifications for multiple recipients.

---

# 9. Notification Model

A notification represents a persistent alert for one user.

It may reference:

```text
who caused it
who receives it
which conversation it concerns
which message caused it
```

## `recipient`

```python
recipient = relationship(
    "User",
    back_populates="received_notifications",
    foreign_keys=[recipient_id],
)
```

This returns the user receiving the notification.

```python
notification.recipient
```

---

## `actor`

```python
actor = relationship(
    "User",
    back_populates="acted_notifications",
    foreign_keys=[actor_id],
)
```

This returns the user who caused the notification.

```python
notification.actor
```

The actor is nullable because system-generated notifications may not have a human actor.

---

## Why `foreign_keys` is required here

`Notification` points to `User` twice:

```text
recipient_id → users.id
actor_id     → users.id
```

Without explicit `foreign_keys`, SQLAlchemy sees two possible paths and cannot reliably determine whether a relationship means recipient or actor.

```python
foreign_keys=[recipient_id]
```

means:

> Use the recipient foreign key for this relationship.

```python
foreign_keys=[actor_id]
```

means:

> Use the actor foreign key for this relationship.

---

## `conversation`

```python
conversation = relationship(
    "Conversation",
    back_populates="notifications",
    foreign_keys=[conversation_id],
)
```

This returns the conversation connected to the notification.

```python
notification.conversation
```

---

## `message`

```python
message = relationship(
    "Message",
    back_populates="notifications",
    foreign_keys=[message_id],
)
```

This returns the message connected to the notification.

```python
notification.message
```

---

# 10. The Conversation–Message Circular Connection

These two tables point at each other:

```text
Message.conversation_id
        ↓
Conversation.id
```

and:

```text
Conversation.last_message_id
        ↓
Message.id
```

This creates a circular dependency:

```text
Conversation needs its last Message.
Message needs its Conversation.
```

## `use_alter=True`

The foreign key is defined as:

```python
ForeignKey(
    "messages.id",
    ondelete="SET NULL",
    use_alter=True,
)
```

This allows SQLAlchemy to handle the circular schema dependency separately when creating or dropping tables.

---

## `post_update=True`

The ORM relationship contains:

```python
post_update=True
```

This tells SQLAlchemy that the special foreign-key value may need to be assigned through an additional update.

Conceptually:

```text
1. Create conversation
2. Create message belonging to conversation
3. Update conversation.last_message_id
```

`post_update` exists for mutually dependent rows where the ORM must perform an additional update after inserting the related records.

The service-layer flow should still be explicit:

```python
conversation = Conversation(...)
session.add(conversation)
await session.flush()

message = Message(
    conversation_id=conversation.id,
    sender_id=user.id,
    ...
)

session.add(message)
await session.flush()

conversation.last_message_id = message.id

await session.commit()
```

---

# 11. Real Application Flows

## Creating a group

```text
1. Create Conversation
2. Set creator
3. Create owner ConversationMember
4. Create member records
5. Create notifications for added members
6. Commit transaction
7. Publish realtime events
```

Created connections:

```text
User.creator → Conversation
User.memberships → ConversationMember
Conversation.memberships → ConversationMember
Notification.recipient → added user
Notification.actor → creator
```

---

## Sending a message

```text
1. Verify sender is an active conversation member
2. Create Message
3. Set Message.conversation
4. Set Message.sender
5. Update Conversation.last_message_id
6. Create recipient notifications
7. Commit transaction
8. Publish WebSocket event
```

Created connections:

```text
Message.sender → User
Message.conversation → Conversation
Conversation.last_message → Message
Notification.message → Message
Notification.conversation → Conversation
```

---

## Replying to a message

```text
1. Load the original message
2. Verify it belongs to the same conversation
3. Create the reply
4. Set reply_to_message_id
```

Connection:

```text
Reply Message.reply_to → Original Message
Original Message.replies → Reply Message
```

---

## Marking a conversation as read

```text
1. Load ConversationMember
2. Verify the message belongs to that conversation
3. Update last_read_message_id
4. Update last_read_at
```

Connection:

```text
ConversationMember.last_read_message → Message
```

Read state belongs to `ConversationMember` because every member reads the conversation independently.

---

# 12. Relationship Collections vs Single Objects

Some relationship properties return lists:

```python
user.memberships
user.sent_messages
conversation.messages
message.replies
```

These represent one-to-many connections.

Other properties return one object or `None`:

```python
message.sender
message.conversation
message.reply_to
notification.recipient
conversation.creator
conversation.last_message
```

These represent many-to-one or optional one-to-one-style connections.

---

# 13. Loading Relationships with Async SQLAlchemy

Declaring a relationship does not mean SQLAlchemy always loads the related data immediately.

For example:

```python
conversation.messages
```

may require another SQL query.

In asynchronous SQLAlchemy code, related objects should usually be loaded explicitly with loader options such as:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload


statement = (
    select(Conversation)
    .options(
        selectinload(Conversation.messages),
        selectinload(Conversation.memberships),
    )
    .where(Conversation.id == conversation_id)
)

result = await session.execute(statement)
conversation = result.scalar_one()
```

`selectinload()` loads related collections in additional controlled queries and helps avoid accidental per-object lazy queries. SQLAlchemy specifically warns that implicit relationship loading requires care with `AsyncSession`; eager loading such as `selectinload()` is the common solution.

Do not automatically load every relationship for every query. Load only what the endpoint needs.

For example:

```text
Conversation list endpoint
├── memberships
└── last message
```

```text
Message history endpoint
├── messages
└── message senders
```

---

# 14. Alembic and Relationships

A `relationship()` is Python ORM configuration.

Adding only this:

```python
sender = relationship("User")
```

does not create a database column.

Therefore, relationship-only changes normally do not produce an Alembic schema migration.

Changes to these do affect the database:

```text
Column
ForeignKey
UniqueConstraint
Index
nullable
server default
Enum
```

Those changes require a migration.

---

# 15. Why Models Are Imported in `models/__init__.py`

Alembic reads:

```python
Base.metadata
```

But a model appears inside `Base.metadata` only after Python imports the model class.

Therefore:

```python
from chatterlite.models.user import User
from chatterlite.models.conversation import Conversation
from chatterlite.models.conversation_member import ConversationMember
from chatterlite.models.message import Message
from chatterlite.models.notification import Notification
```

ensures every table and relationship is registered before Alembic autogeneration runs.

String relationship names such as:

```python
relationship("Conversation")
```

are resolved after the mapped classes have been registered. The string must exactly match the Python class name.

---

# 16. Relationship Validation

Before generating a migration, validate the mappings:

```powershell
poetry run python -c "import chatterlite.models; from sqlalchemy.orm import configure_mappers; configure_mappers(); print('Relationships OK')"
```

Possible errors:

## Class-name error

```text
failed to locate a name 'Conversation'
```

Meaning:

```text
The class is named incorrectly
or
The model was not imported
```

---

## Ambiguous foreign keys

```text
AmbiguousForeignKeysError
```

Meaning:

```text
Two models have multiple foreign-key paths
and SQLAlchemy needs foreign_keys=...
```

---

## Incorrect `back_populates`

```text
back_populates refers to attribute ...
```

Meaning:

```text
The relationship names on both models do not match
```

Example of a correct pair:

```python
User.sent_messages
```

```python
Message.sender
```

```python
sent_messages = relationship("Message" , back_populates="sender")
sender = relationship("User" , back_populates="sent_messages")
```

---

# 17. Final Mental Model

```text
User
│
├── creates Conversation
│
├── joins Conversation through ConversationMember
│
├── sends Message
│
└── receives Notification
│
│
Conversation
│
├── contains ConversationMember records
├── contains Message records
├── points to its latest Message
└── owns related Notification records
│
│
Message
│
├── belongs to Conversation
├── belongs to sender User
├── may reply to another Message
└── may generate Notification records
│
│
Notification
│
├── belongs to recipient User
├── may have an actor User
├── may reference Conversation
└── may reference Message
```

The database foreign keys maintain correctness.

The ORM relationships make the connected records convenient to navigate in Python.

The service layer controls permissions and business rules.

PostgreSQL remains the permanent source of truth, while Redis and WebSockets handle temporary presence and realtime delivery.
