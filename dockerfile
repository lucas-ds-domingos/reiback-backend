# Dockerfile para FastAPI com PDFKit/Wkhtmltopdf
FROM python:3.11-slim

# Evita arquivos .pyc e força saída do Python sem buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Dependências de sistema para wkhtmltopdf, PostgreSQL e fontes
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libpq-dev \
    build-essential \
    curl \
    git \
    xfonts-75dpi \
    xfonts-base \
    libssl-dev \
    libxrender1 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Diretório da aplicação
WORKDIR /app

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar código do backend
COPY . .

# Expõe porta padrão do Railway
EXPOSE 8080

# Comando para rodar o servidor FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
