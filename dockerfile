# Imagem oficial com tudo que o WeasyPrint precisa
FROM weasyprint/weasyprint:latest

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do projeto
COPY . .

# Expor porta do FastAPI
EXPOSE 8000

# Rodar servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
