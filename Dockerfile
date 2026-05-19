FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY loupe /app/loupe

RUN pip install --no-cache-dir . uvicorn

EXPOSE 8000

CMD ["uvicorn", "loupe.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
