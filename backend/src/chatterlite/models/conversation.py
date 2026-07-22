# conversations
# ├── id
# ├── type
# ├── title
# ├── image_url
# ├── direct_key
# ├── created_by
# ├── last_message_id
# ├── created_at
# └── updated_at


import uuid

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import relationship

from chatterlite.models.base import Base
from chatterlite.models.enums import ConversationType


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True) , default=uuid.uuid4 , primary_key=True)
    type = Column(Enum(ConversationType , name="conversation_type") , nullable=False)
    title = Column(String , nullable=True)
    image_url = Column(String , nullable=True)
    direct_key = Column(String , unique=True , nullable=True)
    created_by = Column(UUID(as_uuid=True) , ForeignKey("users.id") , nullable=False)
    last_message_id = Column(UUID(as_uuid=True) , ForeignKey("messages.id" , ondelete="SET NULL" , use_alter=True) , nullable=True)
    created_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone=True) , default=func.now() , onupdate=func.now() , nullable=False)

    creator = relationship("User" , back_populates="created_conversations" , foreign_keys=[created_by])
    memberships = relationship("ConversationMember" , back_populates="conversation")
    messages = relationship("Message" , back_populates="conversation" , foreign_keys="Message.conversation_id")
    last_message = relationship("Message" , foreign_keys=[last_message_id] , post_update=True)
    notifications = relationship("Notification" , back_populates="conversation" , foreign_keys="Notification.conversation_id")