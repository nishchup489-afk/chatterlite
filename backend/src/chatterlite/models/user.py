"""
users
├── id
├── clerk_user_id
├── username
├── display_name
├── avatar_url
├── last_seen_at
├── created_at
└── updated_at

"""


from sqlalchemy import Column , String , DateTime, UUID 
import uuid

from chatterlite.models.base import Base 


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
    )