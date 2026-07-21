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


from sqlalchemy import Column , String , DateTime, UUID, func 
import uuid

from chatterlite.models.base import Base 


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
    )

    clerk_user_id = Column(String , unique=True , nullable=False)
    username = Column(String , nullable=False , unique=True)
    display_name = Column(String , nullable=False)
    avatar_url = Column(String)
    last_seen_at = Column(DateTime(timezone=True) , nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone=True) , default=func.now() ,  onupdate=func.now() , nullable=False)