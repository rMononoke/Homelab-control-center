# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --prefix=/install -r requirements.txt

# Final runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

# Run as non-root user
RUN groupadd -g 10002 botgroup && \
    useradd -u 10002 -g botgroup -s /bin/false -m botuser

COPY --from=builder /install /install
COPY . /app

RUN chown -R botuser:botgroup /app

USER botuser

CMD ["python", "main.py"]
