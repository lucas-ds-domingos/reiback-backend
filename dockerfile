# Usando Python 3.11
FROM python:3.11-slim

# Variáveis de ambiente para não criar arquivos .pyc e buffer de saída
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Dependências de sistema para wkhtmltopdf e PostgreSQL
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libpq-dev \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da aplicação
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar todo o backend
COPY . .

# Expõe a porta padrão do Railway
EXPOSE 8080

# Comando para rodar o servidor FastAPI com Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
