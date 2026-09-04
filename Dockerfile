FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POLIBOT_EXECUTION_MODE=paper \
    POLIBOT_LIVE_TRADING_ENABLED=false

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install .

RUN useradd --create-home --uid 10001 polibot
USER polibot

EXPOSE 8000
CMD ["uvicorn", "polibot.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

