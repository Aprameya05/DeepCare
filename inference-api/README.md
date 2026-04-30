# NexioraDx Inference API

## Run locally

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -r inference-api/requirements.txt`
3. Start API from repo root:
   - `uvicorn inference-api.app.main:app --reload --port 8000`

## Environment variables

- `MODEL_ROOT`: Optional absolute path to model directory.
  - Default: `<repo>/Models`

## Endpoints

- `GET /health`
- `GET /models/status`
- `POST /predict/image` (`multipart/form-data`: `diseaseId`, `image`)
- `POST /predict/params` (`application/json`: `diseaseId`, `parameters`)
