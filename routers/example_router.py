from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database.database import get_session
from models.models import Hero
from repositories.user_repo import get_hero_by_id, get_all_heroes, create_hero

router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("/")
def read_heroes(session: Session = Depends(get_session)) -> list[Hero]:
    """Get all heroes."""
    return get_all_heroes(session)


@router.get("/{hero_id}")
def read_hero(hero_id: int, session: Session = Depends(get_session)) -> Hero:
    """Get a hero by ID."""
    hero = get_hero_by_id(session, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@router.post("/")
def create_new_hero(hero: Hero, session: Session = Depends(get_session)) -> Hero:
    """Create a new hero."""
    return create_hero(session, hero)


@router.get("/example")
def read_example():
    return {"message": "This is an example route"}
