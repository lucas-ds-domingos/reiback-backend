FROM python:3.11-slim

# Instala dependências do sistema para pycairo, playwright e PDF generation
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libgdk-pixbuf2.0-dev \
    libfreetype6-dev \
    libpng-dev \
    libjpeg62-turbo-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Para Playwright: instala browsers (se necessário no build)
RUN playwright install --with-deps chromium

# Copia o código da app
COPY . .

# Expõe a porta (Railway usa $PORT)
EXPOSE $PORT

# Comando de start (ajuste se o seu entrypoint for diferente, ex: uvicorn main:app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT", "--reload"]