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

from sqlalchemy import UUID, Column, DateTime, Enum, String, func

from chatterlite.models.base import Base
from chatterlite.models.enums import ConversationType , MemberRole , MessageType , NotificationType


class Conversations(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True) , default=uuid.uuid8 , primary_key=True)
    type = Column(Enum(ConversationType) , nullable=False)
    title = Column(String , nullable=False)
    image_url = Column(String )
    direct_key = Column(String , nullable=True)
    created_by = Column(String )
    last_message_id = Column(UUID(as_uuid=True) , default=uuid.uuid8 , unique=True)
    created_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone=True) , default=func.now() , onupdate=func.now() , nullable=False)

