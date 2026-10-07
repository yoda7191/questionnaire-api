FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY scales/ scales/

# Run as a non-root user that owns the data folder.
RUN useradd --create-home appuser && mkdir -p data && chown appuser data
USER appuser

EXPOSE 8000
# Hosting platforms often set PORT; fall back to 8000 locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
