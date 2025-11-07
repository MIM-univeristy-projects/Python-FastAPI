import enum
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import TEXT, Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class FriendshipStatusEnum(str, enum.Enum):
    BUDDY = "buddy"
    STRANGER = "stranger"


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control."""

    USER = "user"
    ADMIN = "admin"


class User(SQLModel, table=True):
    """User model for storing user information."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(sa_column=Column(SAEnum(UserRole)), default=UserRole.USER)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now(UTC))


class UserCreate(BaseModel):
    """User creation model for user registration."""

    email: str
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model for returning user data to frontend."""

    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """Token model for authentication responses."""

    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    """Extended token response including user information with role."""

    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Token data model for storing decoded token information."""

    username: str | None = None


class Post(SQLModel, table=True):
    """Post model for storing posts."""

    id: int | None = Field(default=None, primary_key=True)
    text: str = Field(sa_column=Column(TEXT))
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default=datetime.now(UTC))


class Friendship(SQLModel, table=True):
    """Friendship model for managing user friendships."""

    id: int | None = Field(default=None, primary_key=True)
    requester_id: int = Field(foreign_key="user.id")
    addressee_id: int = Field(foreign_key="user.id")
    status: str = Field(
        sa_column=Column(SAEnum(FriendshipStatusEnum)), default=FriendshipStatusEnum.STRANGER
    )


class PostLikes(
    SQLModel,
    table=True,
):
    """PostLikes model for managing likes on posts."""

    __tablename__ = "post_likes"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    text: str = Field(sa_column=Column(TEXT))
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")


class Conversation(SQLModel, table=True):
    """Conversation model for managing conversations."""

    id: int | None = Field(default=None, primary_key=True)
    title: str


class ConversationParticipants(SQLModel, table=True):
    """ConversationParticipants model for managing conversation participants."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")


class Comments(SQLModel, table=True):
    """Comments model for storing comments on posts."""

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    author_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")


class Messages(SQLModel, table=True):
    """Messages model for managing messages in conversations."""

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    sender_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")
