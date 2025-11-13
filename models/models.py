import enum
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import TEXT, Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel  # type: ignore

# ============================================================================
# ENUMERATIONS
# ============================================================================


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control."""

    USER = "user"
    ADMIN = "admin"


class FriendshipStatusEnum(str, enum.Enum):
    """Friendship status enumeration."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


# ============================================================================
# DATABASE MODELS (SQLModel with table=True)
# ============================================================================


class User(SQLModel, table=True):
    """User model for storing user information."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    hashed_password: str
    role: str = Field(sa_column=Column(SAEnum(UserRole)), default=UserRole.USER)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now(UTC))


class Post(SQLModel, table=True):
    """Post model for storing user posts."""

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
        sa_column=Column(SAEnum(FriendshipStatusEnum)), default=FriendshipStatusEnum.PENDING
    )


class PostLikes(SQLModel, table=True):
    """PostLikes model for managing likes on posts."""

    __tablename__ = "post_likes"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")
    created_at: datetime = Field(default=datetime.now(UTC))


class Comments(SQLModel, table=True):
    """Comments model for storing comments on posts."""

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    author_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")
    created_at: datetime = Field(default=datetime.now(UTC))


class Conversation(SQLModel, table=True):
    """Conversation model for managing conversations."""

    id: int | None = Field(default=None, primary_key=True)
    title: str


class ConversationParticipants(SQLModel, table=True):
    """ConversationParticipants model for managing conversation participants."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")


class Messages(SQLModel, table=True):
    """Messages model for managing messages in conversations."""

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(TEXT))
    sender_id: int = Field(foreign_key="user.id")
    conversation_id: int = Field(foreign_key="conversation.id")


# ============================================================================
# REQUEST/RESPONSE MODELS (Pydantic BaseModel)
# ============================================================================


# User-related models
class UserCreate(BaseModel):
    """User creation model for user registration."""

    email: str
    username: str
    first_name: str
    last_name: str
    password: str


class UserResponse(BaseModel):
    """User response model for returning user data to frontend."""

    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime


# Authentication models
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


# Friendship models
class FriendshipResponse(BaseModel):
    """Friendship response model."""

    id: int
    requester_id: int
    addressee_id: int
    status: FriendshipStatusEnum


# Post models
class PostReadWithAuthor(BaseModel):
    """Post model with author information included."""

    id: int
    text: str
    author_id: int
    created_at: datetime
    author: User


class PostLikesResponse(BaseModel):
    """Response model for post likes information."""

    likes_count: int
    liked_by_current_user: bool


# Comment models
class CommentResponse(BaseModel):
    """Response model for comment with author information."""

    id: int
    content: str
    author_id: int
    post_id: int
    created_at: datetime
    author: User


# ============================================================================
# TEST FIXTURE MODELS
# ============================================================================


class AuthenticatedUser(BaseModel):
    """Model for authenticated user with token and headers (used in tests)."""

    user: User
    token: str
    headers: dict[str, str]


class FriendshipScenario(BaseModel):
    """Model for friendship test scenario with user IDs (used in tests)."""

    user_a_id: int
    user_b_id: int
    user_c_id: int
    user_d_id: int
