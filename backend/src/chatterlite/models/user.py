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


import uuid

from sqlalchemy import UUID, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from chatterlite.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True) , default=uuid.uuid4 , primary_key=True)
    clerk_user_id = Column(String , unique=True , nullable=False)
    username = Column(String , unique=True , nullable=False)
    display_name = Column(String , nullable=False)
    avatar_url = Column(String , nullable=True)
    last_seen_at = Column(DateTime(timezone=True) , nullable=True)
    created_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone=True) , default=func.now() , onupdate=func.now() , nullable=False)

    created_conversations = relationship("Conversation" , back_populates="creator" , foreign_keys="Conversation.created_by")
    memberships = relationship("ConversationMember" , back_populates="user")
    sent_messages = relationship("Message" , back_populates="sender" , foreign_keys="Message.sender_id")
    received_notifications = relationship("Notification" , back_populates="recipient" , foreign_keys="Notification.recipient_id")
    acted_notifications = relationship("Notification" , back_populates="actor" , foreign_keys="Notification.actor_id")