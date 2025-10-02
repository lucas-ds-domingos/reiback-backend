FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libgdk-pixbuf2.0-bin \
    libglib2.0-0 \
    libglib2.0-dev \
    libharfbuzz0b \
    libharfbuzz-dev \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    zlib1g \
    fonts-liberation \
    fonts-dejavu \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-cache-dir -r requirements.txt

# Copiar projeto
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
