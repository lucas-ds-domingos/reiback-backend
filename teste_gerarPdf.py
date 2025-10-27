import asyncio
from app.routers.gerarPdfComisao import gerar_pdf, preparar_html

# ---------------------------
# Dados fictícios para teste
# ---------------------------
dados = [
    {
        "numero_apolice": "12345",
        "tomador_nome": "Empresa Exemplo LTDA",
        "segurado_nome": "João da Silva",
        "premio": 1500.50,
        "percentual": 20,
        "comissao_valor": 300.10,
    },
    {
        "numero_apolice": "FIN-00083",
        "tomador_nome": "PETROS STONES MINERAIS DO BRASIL LTDA",
        "segurado_nome": "DEPARTAMENTO DE ESTRADAS DE RODAGEM DO PIAUI",
        "premio": 2189973.89,
        "percentual": 20,
        "comissao_valor": 437994.778,
    },
]

numero_demonstrativo = "001/2025"

# ---------------------------
# Main
# ---------------------------
def main():
    html = preparar_html(dados, numero_demonstrativo)
    asyncio.run(gerar_pdf(html, output_path="comissao_teste_local.pdf"))

if __name__ == "__main__":
    main()
