from sqlmodel import Field, SQLModel
from sqlmodel import create_engine

postgres_url = "postgresql://postgres:postgres@postgres-devcontainer:5432/postgres"
engine = create_engine(postgres_url, echo=True)


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: int
    age: int | None = None


SQLModel.metadata.create_all(engine)


# def test_select():
#     with Session(engine) as session:
#         statement = select(Hero)
#         result = session.exec(statement)
#         print(result.all())


# if __name__ == "__main__":
# test_select()
