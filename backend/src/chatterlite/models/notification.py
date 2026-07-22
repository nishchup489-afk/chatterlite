# notifications
# ├── id
# ├── recipient_id
# ├── actor_id
# ├── type
# ├── conversation_id
# ├── message_id
# ├── title
# ├── body
# ├── is_read
# ├── created_at
# └── read_at

import uuid

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import relationship

from chatterlite.models.base import Base
from chatterlite.models.enums import NotificationType


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True) , default=uuid.uuid4 , primary_key=True)
    recipient_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False , index=True)
    actor_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="SET NULL") , nullable=True)
    type = Column(Enum(NotificationType , name="notification_type") , nullable=False)
    conversation_id = Column(UUID(as_uuid=True) , ForeignKey("conversations.id" , ondelete="SET NULL") , nullable=True)
    message_id = Column(UUID(as_uuid=True) , ForeignKey("messages.id" , ondelete="SET NULL") , nullable=True)
    title = Column(String , nullable=False)
    body = Column(String , nullable=False)
    is_read = Column(Boolean , default=False , nullable=False)
    created_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    read_at = Column(DateTime(timezone=True) , nullable=True)

    recipient = relationship("User" , back_populates="received_notifications" , foreign_keys=[recipient_id])
    actor = relationship("User" , back_populates="acted_notifications" , foreign_keys=[actor_id])
    conversation = relationship("Conversation" , back_populates="notifications" , foreign_keys=[conversation_id])
    message = relationship("Message" , back_populates="notifications" , foreign_keys=[message_id])