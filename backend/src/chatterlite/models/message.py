# messages
# ├── id
# ├── conversation_id
# ├── sender_id
# ├── client_message_id
# ├── message_type
# ├── content
# ├── reply_to_message_id
# ├── created_at
# ├── edited_at
# └── deleted_at


import uuid

from sqlalchemy import UUID, Column, DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from chatterlite.models.base import Base
from chatterlite.models.enums import MessageType


class Message(Base):
    __tablename__ = "messages"

    __table_args__ = (UniqueConstraint("sender_id" , "client_message_id" , name="uq_messages_sender_id_client_message_id"),)

    id = Column(UUID(as_uuid=True) , default=uuid.uuid4 , primary_key=True)
    conversation_id = Column(UUID(as_uuid=True) , ForeignKey("conversations.id" , ondelete="CASCADE") , nullable=False , index=True)
    sender_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False , index=True)
    client_message_id = Column(UUID(as_uuid=True) , nullable=False)
    message_type = Column(Enum(MessageType , name="message_type") , default=MessageType.TEXT , nullable=False)
    content = Column(Text , nullable=True)
    reply_to_message_id = Column(UUID(as_uuid=True) , ForeignKey("messages.id" , ondelete="SET NULL") , nullable=True , index=True)
    created_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    edited_at = Column(DateTime(timezone=True) , nullable=True)
    deleted_at = Column(DateTime(timezone=True) , nullable=True)

    conversation = relationship("Conversation" , back_populates="messages" , foreign_keys=[conversation_id])
    sender = relationship("User" , back_populates="sent_messages" , foreign_keys=[sender_id])
    reply_to = relationship("Message" , back_populates="replies" , foreign_keys=[reply_to_message_id] , remote_side=[id])
    replies = relationship("Message" , back_populates="reply_to" , foreign_keys=[reply_to_message_id])
    notifications = relationship("Notification" , back_populates="message" , foreign_keys="Notification.message_id")