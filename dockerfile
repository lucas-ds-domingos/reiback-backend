FROM python:3.11-bookworm

# Deps do sistema para WeasyPrint (Cairo, fontes, etc.)
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
    fonts-dejavu-core \
    libpng-dev \
    libjpeg62-turbo-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Instala browsers para Playwright (se usado)
RUN playwright install --with-deps chromium

# Copia código, templates e static
COPY . .

EXPOSE $PORT

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"]