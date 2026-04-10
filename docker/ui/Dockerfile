FROM python:3.12-slim

WORKDIR /app

COPY requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt

COPY src ./src

ENV API_URL=http://api:8080

CMD ["python", "-m", "src.ui.app"]
