# --- Imagem base Python 3.11 ---
FROM python:3.11-slim

# --- Dependências do sistema para Chromium/Playwright ---
RUN apt-get update && apt-get install -y \
    curl gnupg libnss3 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 \
    libatk1.0-0 libcups2 libdrm2 libxss1 fonts-liberation libappindicator3-1 \
    xdg-utils wget \
    && rm -rf /var/lib/apt/lists/*

# --- Diretório da aplicação ---
WORKDIR /app

# --- Copia requirements e instala venv ---
COPY requirements.txt .
RUN python -m venv /app/venv311
ENV PATH="/app/venv311/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# --- Copia todo o backend ---
COPY . .

# --- Instala Playwright + Chromium com dependências ---
RUN pip install playwright
RUN playwright install --with-deps chromium

# --- Expõe a porta padrão Railway ---
EXPOSE 8080

# --- Comando para rodar ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
