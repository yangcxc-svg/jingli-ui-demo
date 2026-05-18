FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

COPY . /app

RUN mkdir -p /app/storage/uploads && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

