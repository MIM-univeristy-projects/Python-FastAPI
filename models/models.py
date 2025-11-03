from datetime import datetime

from sqlmodel import Field, SQLModel


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    username: str = Field(unique=True)
    hashed_password: str
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
