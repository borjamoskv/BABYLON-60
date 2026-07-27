FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# system deps (minimal)
RUN apt-get update && apt-get install -y curl postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# non-root
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
