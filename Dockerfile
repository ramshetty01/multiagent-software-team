FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mast ./mast
COPY scripts ./scripts

RUN python -m pip install --no-cache-dir -e .

ENTRYPOINT ["python3", "-m", "mast.cli"]

