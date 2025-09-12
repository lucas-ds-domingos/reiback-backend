from fastapi import FastAPI
from .database import Base, engine 
from .models import * 
app = FastAPI()

@app.on_event("startup")
def create_db_tables():
    print("Iniciando a criação das tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")

@app.get("/")
def read_root():
    return {"message": "API funcionando 🚀"}
