FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY src ./src
COPY models ./models

EXPOSE 8080

CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8080"]
