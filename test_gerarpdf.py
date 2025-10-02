from pathlib import Path
from app.routers.gerarpdf import preparar_html, gerar_pdf_playwright

# Simule uma "proposta" de teste
class Dummy:
    def __init__(self):
        self.numero = 123
        self.inicio_vigencia = None
        self.termino_vigencia = None
        self.dias_vigencia = 30
        self.importancia_segurada = 10000
        self.premio = 500
        self.modalidade = "Teste"
        self.subgrupo = "Subgrupo"
        self.numero_contrato = "123/2025"
        self.edital_processo = "EP-01"
        self.percentual = 10
        self.tomador = type("T", (), {"nome":"Lucas","cnpj":"12345678000199","endereco":"Rua X","uf":"SP","municipio":"São Paulo","cep":"01000-000"})()
        self.segurado = type("S", (), {"nome":"Empresa Y","cpf_cnpj":"12345678000100","logradouro":"Rua Y","numero":"100","complemento":"Sala 1","bairro":"Centro","municipio":"São Paulo","uf":"SP","cep":"01000-001"})()
        self.usuario = type("U", (), {"nome":"Admin","email":"admin@teste.com"})()
        self.text_modelo = "Texto padrão do modelo"

proposta = Dummy()

# Gerar HTML
html_content = preparar_html(proposta, None)

# Gerar PDF
pdf_bytes = gerar_pdf_playwright(html_content)

# Salvar local
output_path = Path("proposta_teste.pdf")
with open(output_path, "wb") as f:
    f.write(pdf_bytes)

print(f"PDF salvo em: {output_path.resolve()}")
