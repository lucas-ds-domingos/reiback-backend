# Use Python 3.11 oficial
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Dependências de build + bibliotecas do WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    libcairo2 \
    pango1.0 \
    libgdk-pixbuf2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Diretório do app
WORKDIR /app

# Copia requirements e instala
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copia projeto
COPY . .

# Expõe porta
EXPOSE 8000

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
