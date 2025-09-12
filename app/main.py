from fastapi import FastAPI
from .database import Base, engine  # Importa a Base e o engine do seu arquivo de configuração
from .models import * # Importa todos os seus modelos para que o SQLAlchemy os conheça

app = FastAPI()

# Este é o evento de startup. Ele é executado uma vez, quando a aplicação inicia.
# Base.metadata.create_all(bind=engine) cria todas as tabelas
# definidas nos seus modelos.
@app.on_event("startup")
def create_db_tables():
    print("Iniciando a criação das tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

@app.get("/")
def read_root():
    return {"message": "API funcionando 🚀"}
