from sqlalchemy.orm import Session
from models import Corretora
from schemas import CorretoraCreate

def create_corretora(db: Session, corretora_data: CorretoraCreate):
    nova_corretora = Corretora(**corretora_data.dict())
    db.add(nova_corretora)
    db.commit()
    db.refresh(nova_corretora)
    return nova_corretora
