FROM python:3.11-slim AS builder
WORKDIR /src
RUN pip install --upgrade pip && \
    pip install --no-cache-dir uv==0.9.15
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache

FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y curl --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY --from=builder /src/.venv /src/.venv
COPY ./src /src
RUN useradd -m appuser && chown -R appuser:appuser /src
USER appuser
ENV PATH="/src/.venv/bin:$PATH"
ENV PYTHONPATH=/src
EXPOSE 8000 
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1
CMD [ "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000" ]