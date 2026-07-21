# conversation_members
# ├── id
# ├── conversation_id
# ├── user_id
# ├── role
# ├── last_read_message_id
# ├── last_read_at
# ├── is_muted
# ├── joined_at
# └── left_at

import uuid

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, UniqueConstraint, func

from chatterlite.models.base import Base
from chatterlite.models.enums import MemberRole


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    __table_args__ = (UniqueConstraint("conversation_id" , "user_id" , name="uq_conversation_members_conversation_id_user_id"),)

    id = Column(UUID(as_uuid=True) , default=uuid.uuid4 , primary_key=True)
    conversation_id = Column(UUID(as_uuid=True) , ForeignKey("conversations.id" , ondelete="CASCADE") , nullable=False , index=True)
    user_id = Column(UUID(as_uuid=True) , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False , index=True)
    role = Column(Enum(MemberRole , name="member_role") , default=MemberRole.MEMBER , nullable=False)
    last_read_message_id = Column(UUID(as_uuid=True) , ForeignKey("messages.id" , ondelete="SET NULL") , nullable=True)
    last_read_at = Column(DateTime(timezone=True) , nullable=True)
    is_muted = Column(Boolean , default=False , nullable=False)
    joined_at = Column(DateTime(timezone=True) , default=func.now() , nullable=False)
    left_at = Column(DateTime(timezone=True) , nullable=True)