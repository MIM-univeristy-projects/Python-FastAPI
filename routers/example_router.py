from fastapi import APIRouter, Depends
from sqlmodel import Session

from database.database import get_session

router = APIRouter(prefix="/example", tags=["example"])

session: Session = Depends(get_session)


@router.get("/")
def read_example():
    return {"message": "This is an example route"}
