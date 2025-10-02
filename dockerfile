# Use Python 3.11 oficial
FROM python:3.11-slim

# Evita prompts interativos durante instalações
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza pacotes e instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório do app
WORKDIR /app

# Copia apenas requirements para cache
COPY requirements.txt .

# Instala as dependências
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

# Expõe a porta do FastAPI
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
