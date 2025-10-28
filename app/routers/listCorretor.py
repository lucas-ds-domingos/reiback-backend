from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario, Corretora, Assessoria

router = APIRouter()

@router.get("/corretores/lista")
def listar_corretores(
    db: Session = Depends(get_db),
    somente_ativos: bool = True
):
    """
    Lista todos os corretores, trazendo:
    - Dados do usuário
    - Dados da corretora
    - Nome da assessoria, caso exista vínculo
    """

    query = db.query(Usuario).join(Corretora, Usuario.corretora_id == Corretora.id, isouter=True)\
                            .join(Assessoria, Usuario.assessoria_id == Assessoria.id, isouter=True)\
                            .filter(Usuario.role == "corretor")

    if somente_ativos:
        query = query.filter(Usuario.ativo == True)

    corretores = query.all()

    resultado = []
    for corretor in corretores:
        resultado.append({
            "usuario": {
                "id": corretor.id,
                "nome": corretor.nome,
                "email": corretor.email,
                "ativo": corretor.ativo,
                "role": corretor.role,
            },
            "corretora": {
                "id": corretor.corretora.id if corretor.corretora else None,
                "razao_social": corretor.corretora.razao_social if corretor.corretora else None,
                "cnpj": corretor.corretora.cnpj if corretor.corretora else None,
            },
            "assessoria": {
                "id": corretor.assessoria.id if corretor.assessoria else None,
                "razao_social": corretor.assessoria.razao_social if corretor.assessoria else None
            }
        })

    return {"corretores": resultado}
