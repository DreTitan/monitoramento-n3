FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro (para cache)
COPY backend/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ .

# Expor porta
EXPOSE 8000

# Comando para produção
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
