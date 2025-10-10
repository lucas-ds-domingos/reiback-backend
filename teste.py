import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from app.services.gerar_ccg_pdf import gerar_pdf_ccg  # nome atualizado
from app.services.d4sign_service import enviar_para_d4sign

# 🔹 Carrega variáveis de ambiente do .env
load_dotenv()

# Caminho para salvar PDF localmente (opcional)
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
            "nome": "ADEMAR ABRÃO FILHO",
            "cpf": "572.211.709-91",
            "estado_civil": "Casado",
            "profissao": "Empresário",
            "endereco": "Rua Espírito Santo, 1570",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "pendencia@reibacknegocios.com.br"
        },
        {
            "nome": "ROSEMEYRE CLAUDIO MASTELLINI",
            "cpf": "033.239.569-31",
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
            "nome": "THAIS DE MELLO COSTA ALVES",
            "cpf": "093.623.739-20",
            "estado_civil": "Solteira",
            "profissao": "Empresária",
            "endereco": "Rua Belo Horizonte, 1445",
            "cidade": "Londrina",
            "uf": "PR",
            "email": "lukinhascraftman@gmail.com"
        },
        {
            "nome": "RAFAEL DOMINGOS",
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
    print(f"✅ PDF gerado com sucesso: {output_pdf}")

    print("✉️ Enviando para D4Sign...")
    resultado = await enviar_para_d4sign(pdf_bytes, dados_teste)

    print("✅ Documento enviado com sucesso para D4Sign!")
    print(f"📄 UUID do documento: {resultado['uuid']}")

    # Exibe links de assinatura (caso o envio por e-mail não esteja ativo)
    if "links_assinatura" in resultado:
        for l in resultado["links_assinatura"]:
            print(f"{l['email']} → {l['link']}")


if __name__ == "__main__":
    asyncio.run(main())
