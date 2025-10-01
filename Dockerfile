# Usar Python 3.11 slim
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libasound2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    xdg-utils \
    libglib2.0-0 \
    curl \
    wget \
    unzip \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores do Playwright
RUN python -m playwright install --with-deps

# Copiar todo o código da pasta backend para /app
COPY . .

# Comando para rodar FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
