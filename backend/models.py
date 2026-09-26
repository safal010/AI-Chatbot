from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    role = Column(String)
    chat_id = Column(Integer, ForeignKey("chats.id"))