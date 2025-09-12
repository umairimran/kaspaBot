FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# System deps for pdf, sqlite, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install lighter packages first
COPY requirements.txt ./requirements.txt

# Install heavy packages (like playwright) separately to avoid timeout
RUN pip install --no-cache-dir --retries 5 playwright \
    && pip install --no-cache-dir --retries 5 -r requirements.txt --no-deps

# Copy project files
COPY backend ./backend
COPY embeddings ./embeddings

# Default environment variables; override via compose
ENV USE_QDRANT=true \
    QDRANT_HOST=qdrant \
    QDRANT_PORT=6333 \
    BACKEND_BIND_URL=http://0.0.0.0:8000 \
    BACKEND_URL=http://kaspa-backend:8000

EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "main.py"]
