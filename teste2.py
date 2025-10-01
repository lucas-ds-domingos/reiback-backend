# teste_pdf_local.py
from app.services.pdf_service import montar_html_apolice, gerar_pdf_playwright
from app.models import SessionLocal, Proposta

def main():
    # Cria sessão com o banco
    session = SessionLocal()

    try:
        # ID da proposta que quer gerar
        id_apolice = 18
        proposta = session.query(Proposta).filter(Proposta.id == id_apolice).first()

        if not proposta:
            print(f"❌ Proposta {id_apolice} não encontrada")
            return

        # Monta HTML e gera PDF
        html = montar_html_apolice(proposta)
        pdf_bytes = gerar_pdf_playwright(html)

        # Salva PDF localmente
        with open("teste_apolice.pdf", "wb") as f:
            f.write(pdf_bytes)

        print("✅ PDF gerado com sucesso em teste_apolice.pdf")

    finally:
        session.close()

if __name__ == "__main__":
    main()
