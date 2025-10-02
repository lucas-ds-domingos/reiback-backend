FROM python:3.11-slim

# Instala libs do sistema para WeasyPrint (Cairo, Pango, fontes, etc.) - resolve "cairo not found"
RUN apt-get update && apt-get install -y \
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
    fonts-dejavu-core \
    libpng-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia e instala Python deps (sem cache para evitar issues)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala browser para Playwright (se usado em outras rotas)
RUN playwright install --with-deps chromium

# Copia o código (inclui templates e static)
COPY . .

# Expõe porta (Railway usa $PORT)
EXPOSE $PORT

# Start command - ajuste 'main:app' para o seu (ex: app:app se arquivo for app.py)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]