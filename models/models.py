import enum
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import TEXT, Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class FriendshipStatusEnum(str, enum.Enum):
    BUDDY = "buddy"
    STRANGER = "stranger"


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None


class User(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class Post(SQLModel, table=True):
    id: int = Field(primary_key=True)
    text: str = Field(sa_column=Column(TEXT))
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Friendship(SQLModel, table=True):
    id: int = Field(primary_key=True)
    requester_id: int = Field(foreign_key="user.id")
    addressee_id: int = Field(foreign_key="user.id")
    status: str = Field(
        sa_column=Column(SAEnum(FriendshipStatusEnum)), default=FriendshipStatusEnum.STRANGER
    )


class PostLikes(
    SQLModel,
    table=True,
):
    __tablename__ = "post_likes"  # type: ignore
    id: int = Field(primary_key=True)
    text: str = Field(sa_column=Column(TEXT))
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")


class Conversation(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str


class ConversationParticipants(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")


class Comments(SQLModel, table=True):
    id: int = Field(primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    author_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")


class Messages(SQLModel, table=True):
    id: int = Field(primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    sender_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")
