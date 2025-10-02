# ==========================
# Base Python 3.11 slim
# ==========================
FROM python:3.11-slim

# ==========================
# Variáveis de ambiente
# ==========================
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ==========================
# Dependências do sistema
# ==========================
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libpango-1.0-0 \
    libgtk-3-0 \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libxshmfence1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ==========================
# Criar diretório da aplicação
# ==========================
WORKDIR /app

# ==========================
# Copiar requirements
# ==========================
COPY requirements.txt .

# ==========================
# Instalar dependências Python
# ==========================
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ==========================
# Copiar código da aplicação
# ==========================
COPY . .

# ==========================
# Instalar browsers do Playwright
# ==========================
RUN python -m playwright install

# ==========================
# Porta padrão do Railway
# ==========================
EXPOSE 8080

# ==========================
# Rodar servidor FastAPI
# ==========================
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
