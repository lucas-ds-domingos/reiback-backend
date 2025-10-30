import asyncio
from datetime import datetime
from app.routers.gerarPdfPagoAssessoria import preparar_html, gerar_pdf

async def main():
    # --- Dados fictícios ---
    dados_por_dia = {
        datetime(2025, 10, 1): [
            {
                "apolice_numero": "123456",
                "tomador_nome": "Empresa Alpha LTDA",
                "segurado_nome": "João da Silva",
                "corretor_nome": "Maria Corretora",
                "valor_premio": 1500.00,
                "percentual_assessoria": 10.0,
                "valor_assessoria": 150.00
            },
            {
                "apolice_numero": "654321",
                "tomador_nome": "Beta Financeira",
                "segurado_nome": "Carlos Pereira",
                "corretor_nome": "Maria Corretora",
                "valor_premio": 2000.00,
                "percentual_assessoria": 8.0,
                "valor_assessoria": 160.00
            },
        ],
        datetime(2025, 10, 2): [
            {
                "apolice_numero": "999111",
                "tomador_nome": "Seguradora XYZ",
                "segurado_nome": "Ana Oliveira",
                "corretor_nome": "Pedro Silva",
                "valor_premio": 3500.00,
                "percentual_assessoria": 12.0,
                "valor_assessoria": 420.00
            }
        ]
    }

    # Número de demonstrativo fictício
    numero_demonstrativo = "000123"

    # --- Gera HTML ---
    html_content = preparar_html(
        dados={
            "nome_assessoria": "Assessoria Confiança",
            "cnpj": "22.333.444/0001-55",
            "endereco": "Rua das Laranjeiras, 500",
            "cep": "04567-000",
            "cidade": "São Paulo",
            "uf": "SP",
            "email": "contato@assessoriaconfianca.com",
            "dados_por_dia": dados_por_dia,
        },
        numero_demonstrativo=numero_demonstrativo
    )

    # --- Gera PDF ---
    output_path = "teste_comissao.pdf"
    print("🧾 Gerando PDF de teste...")
    await gerar_pdf(html_content, output_path)
    print(f"✅ PDF gerado com sucesso: {output_path}")

# Executa
if __name__ == "__main__":
    asyncio.run(main())
