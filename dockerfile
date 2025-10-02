FROM python:3.11

# Instala dependências do sistema para pycairo, freetype-py, playwright e geração de PDF (CairoSVG/WeasyPrint-like)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    libfreetype6-dev \
    libfontconfig1-dev \
    fonts-liberation \
    libpng-dev \
    libjpeg62-turbo-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia e instala requirements (usa --no-cache para evitar cache inválido)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala browsers para Playwright (se usado na rota de PDF ou testes)
RUN playwright install --with-deps chromium

# Copia o resto do código
COPY . .

# Expõe a porta (Railway injeta $PORT automaticamente)
EXPOSE $PORT

# Comando de start: Ajuste "main:app" para o seu arquivo principal (ex: se for app.py, use "app.main:app")
# Remova --reload em produção
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"]