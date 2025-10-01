# Base Python 3.11 slim
FROM python:3.11-slim

# Dependências do sistema para Chromium + Playwright
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg \
    libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 libasound2 libgbm1 \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libgtk-3-0 libxrender1 fonts-liberation xdg-utils libglib2.0-0 \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar todo o código da aplicação
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium do Playwright com dependências
RUN python -m playwright install chromium --with-deps

# Comando para rodar FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
