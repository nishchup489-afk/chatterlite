import uuid

from sqlalchemy import Column , String , Integer , ForeignKey , UUID, Text , DateTime, func
from sqlalchemy.orm import relationship 
from src.core.database import Base


# id
# clerk_user_id
# username
# display_name
# email
# avatar_url
# bio
# created_at
# updated_at


class User(Base):
    __tablename__ = "user_table"

    id = Column(UUID(as_uuid=True) , default=uuid.uuid8() , primary_key=True)
    clerk_user_id = Column(String , nullable=False , unique=True)
    username = Column(String , nullable=False , unique=True)
    display_name = Column(String , nullable= False)
    email = Column(String , nullable=False , unique=True)
    avatar_url = Column(String )
    bio = Column(Text)
    created_at = Column(DateTime(timezone=True) , server_default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone=True) , server_default=func.now() , onupdate=func.now() , nullable= False)


    message_id = Column(UUID(as_uuid=True) , ForeignKey("Message.id"))

    message = relationship("user" , back_populates="message" )