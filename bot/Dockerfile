FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /var/lock/fitminiapp-bot \
    && chown -R appuser:appuser /app /var/lock/fitminiapp-bot
USER appuser
CMD ["python", "-m", "app.bot"]
