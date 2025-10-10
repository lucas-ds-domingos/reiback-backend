import asyncio
from pathlib import Path
from dotenv import load_dotenv
from app.services.gerar_ccg_pdf import gerar_pdf_ccg  # nome atualizado

# 🔹 Carrega variáveis de ambiente do .env (opcional, se o gerar_pdf_ccg usa .env)
load_dotenv()

# Caminho para salvar PDF localmente
output_pdf = Path(__file__).parent / "ccg_teste.pdf"

# ⚙️ Dados de exemplo
dados_teste = {
    "tomador": {
        "nome": "SAN MIGUEL COM. DE PAES LTDA",
        "cnpj": "00.147.733/0001-53",
        "endereco": "Av. Higienópolis, 762",
        "municipio": "Londrina",
        "uf": "PR"
    },
    "fiadores": [
        {
            "nome_completo": "ADEMAR ABRÃO FILHO",
            "cpf_cnpj": "572.211.709-91",
            "estado_civil": "Casado",
            "profissao": "Empresário",
            "endereco": "Rua Espírito Santo, 1570",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "pendencia@reibacknegocios.com.br"
        },
        {
            "nome_completo": "ROSEMEYRE CLAUDIO MASTELLINI",
            "cpf_cnpj": "033.239.569-31",
            "estado_civil": "Solteira",
            "profissao": "Empresária",
            "endereco": "Rua Belo Horizonte, 1445",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "lucasdomingos.ds@hotmail.com"
        }
    ],
    "representantes_legais": [
        {
            "nome_completo": "THAIS DE MELLO COSTA ALVES",
            "cpf": "093.623.739-20",
            "estado_civil": "Solteira",
            "profissao": "Empresária",
            "endereco": "Rua Belo Horizonte, 1445",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "lukinhascraftman@gmail.com"
        },
        {
            "nome_completo": "RAFAEL DOMINGOS",
            "cpf": "111.222.333-44",
            "estado_civil": "Casado",
            "profissao": "Advogado",
            "endereco": "Rua Sergipe, 1200",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "lukinhascraftman2@gmail.com"
        }
    ]
}

async def main():
    print("🧩 Gerando PDF da CCG...")
    pdf_bytes = await gerar_pdf_ccg(dados_teste)

    # Salva localmente
    output_pdf.write_bytes(pdf_bytes)
    print(f"✅ PDF salvo com sucesso em: {output_pdf.resolve()}")

    print("🔍 Agora abra o arquivo e veja se os REPRESENTANTES e FIADORES estão aparecendo nas assinaturas corretamente.")

if __name__ == "__main__":
    asyncio.run(main())
