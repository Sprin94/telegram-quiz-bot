from datetime import datetime

from sqlalchemy.ext.declarative import declared_attr, as_declarative
from sqlalchemy import (
    Column, DateTime, Integer, Text, String, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship


@as_declarative()
class Base:
    id = Column(
        Integer,
        primary_key=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


class Chat(Base):
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=False
    )
    name = Column(
        String(50),
    )
    questions = relationship('Question', back_populates='chat')


class Question(Base):
    text = Column(Text)
    chat_id = Column(
        Integer,
        ForeignKey('chats.id', ondelete="CASCADE"),
        nullable=False,
    )

    chat = relationship('Chat', back_populates='questions')
    answers = relationship('Answer', back_populates='question')


class Answer(Base):
    id = Column(
        Integer,
        primary_key=True
    )
    text = Column(
        Text,
        nullable=False
    )
    is_right = Column(
        Boolean,
        nullable=False
    )
    question_id = Column(
        Integer,
        ForeignKey('questions.id', ondelete="CASCADE"),
        nullable=False,
    )
    question = relationship('Question', back_populates='answers')
