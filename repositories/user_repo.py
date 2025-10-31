from sqlmodel import Session, select
from models.models import Hero


def get_hero_by_id(session: Session, hero_id: int) -> Hero | None:
    """Get a hero by ID using a provided session."""
    return session.get(Hero, hero_id)


def get_all_heroes(session: Session) -> list[Hero]:
    """Get all heroes using a provided session."""
    statement = select(Hero)
    return list(session.exec(statement).all())


def create_hero(session: Session, hero: Hero) -> Hero:
    """Create a new hero using a provided session."""
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero
