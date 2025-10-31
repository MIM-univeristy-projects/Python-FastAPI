from sqlmodel import create_engine, Session
from sqlalchemy import Engine

postgres_url = "postgresql://postgres:postgres@postgres-devcontainer:5432/postgres"
engine: Engine = create_engine(postgres_url, echo=True)


def get_session():
    with Session(engine) as session:
        yield session
