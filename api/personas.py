from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from db import get_db_session
from repositories.persona_repo import get_all_personas
from schemas import PersonaOut

router = APIRouter(tags=["personas"])


@router.get("/personas", response_model=list[PersonaOut])
def get_personas(db: Session = Depends(get_db_session)):
    return get_all_personas(db)  # Ensure the database session is available
