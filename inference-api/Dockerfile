FROM python:3.10-slim

WORKDIR /app

COPY inference-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY inference-api /app/inference-api
COPY Models /app/Models

ENV MODEL_ROOT=/app/Models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/app/inference-api", "--host", "0.0.0.0", "--port", "8000"]
