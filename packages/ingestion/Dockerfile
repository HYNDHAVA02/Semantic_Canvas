FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY packages/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/ingestion/src/ src/

CMD ["python", "-m", "src.main"]
