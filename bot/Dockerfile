# syntax=docker/dockerfile:1

FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /var/lock/fitminiapp-bot \
    && chown appuser:appuser /var/lock/fitminiapp-bot
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "-m", "fitminiapp_bot.bot"]
