# Usa imagem oficial do WeasyPrint (já inclui Cairo, Pango, GObject, GTK, fontes e libs necessárias)
FROM weasyprint/weasyprint:latest

# Diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instala Chromium para Playwright (se você usar Playwright)
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

# Copia o código do backend
COPY . .

# Expor a porta que o Render vai usar
EXPOSE 10000

# Start command
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
