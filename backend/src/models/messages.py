import uuid

from sqlalchemy import JSON, Boolean, Column , String , Integer , ForeignKey , UUID, Text , DateTime, func
from sqlalchemy.orm import relationship 
from src.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True) , ForeignKey("User.id"))

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content = Column(Text, nullable=True)

    message_type = Column(
        String(30),
        nullable=False,
        default="text",
    )
    # text, image, file, audio, system, agent

    metadata = Column(JSON, nullable=True)
    # optional: file url, file name, image width/height, agent info, etc.

    reply_to_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_edited = Column(Boolean, nullable=False, default=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    user = relationship("message" , back_populates="user" )