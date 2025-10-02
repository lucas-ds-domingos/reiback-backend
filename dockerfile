FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    libfreetype6-dev \
    libfontconfig1-dev \
    libglib2.0-dev \         
    libgobject2.0-0 \         
    shared-mime-info \        
    fonts-liberation \
    fonts-dejavu-core \
    libpng-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libgtk-3-0 \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*  # Limpa cache para imagem menor

# Diretório de trabalho
WORKDIR /app

# Copia e instala Python deps (sem cache para evitar issues)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala browser para Playwright (se usado em outras rotas) - faça após apt para evitar conflitos
RUN playwright install --with-deps chromium
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH


# Copia o código (inclui templates e static)
COPY . .

# Expõe porta padrão (Railway usa $PORT em runtime; isso é opcional)
EXPOSE 8080

# Start command - usa $PORT da Railway (fallback para 8000 se não setado)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]