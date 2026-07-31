from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from db import get_db_session
from repositories.persona_repo import db_get_all_personas
from schemas import PersonaOut

router = APIRouter(tags=["personas"])


@router.get("/personas", response_model=list[PersonaOut])
def get_personas(db: Session = Depends(get_db_session)):
    personas = db_get_all_personas(db)
    if not personas:
        raise HTTPException(status_code=500, detail="Internal Server Error: No personas found in the database.")
    return personas
