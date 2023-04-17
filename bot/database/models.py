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


class Question(Base):
    text = Column(Text)
    chat_id = Column(
        Integer,
        ForeignKey('chats.id', ondelete="CASCADE"),
        nullable=False,
    )

    chat = relationship('Chats', backref='questions')


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
        ForeignKey('questions.id'),
        nullable=False
    )
    question = relationship('Question', backref='answers')
