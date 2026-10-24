FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir .

EXPOSE 8000

# Applies migrations before serving. Fine for a single backend instance;
# for multi-instance deploys, run `alembic upgrade head` as a separate
# release/pre-deploy step instead (see docs/deployment.md).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
