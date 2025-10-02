FROM python:3.11

# Instala dependências do sistema para WeasyPrint e Playwright
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libglib2.0-dev \
    libgobject-2.0-0 \
    libgtk-3-0 \
    libgirepository1.0-dev \
    libgirepository1.0-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-color-emoji \
    libpng-dev \
    libjpeg62-turbo-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Garantir que Python encontre libs nativas
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Diretório de trabalho
WORKDIR /app

# Copia e instala Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala Chromium para Playwright (se usado)
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

# Copia o código
COPY . .

# Porta padrão do Render
EXPOSE 10000

# Start command
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
