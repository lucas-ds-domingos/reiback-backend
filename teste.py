import os
from dotenv import load_dotenv
from app.routers.d4sign_tasks import enviar_para_d4sign_e_salvar
from app.database import SessionLocal
from app.models import Apolice

load_dotenv()

def main():
    # Escolha aqui o ID de uma apólice de teste existente no seu banco
    apolice_id_teste = 18

    print(f"🚀 Testando envio para D4Sign com apólice {apolice_id_teste}...")
    enviar_para_d4sign_e_salvar(apolice_id_teste)

if __name__ == "__main__":
    main()
