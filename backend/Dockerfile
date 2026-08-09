FROM node:26-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
COPY backend/requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY backend/ .
COPY --from=frontend-build /frontend/dist /app/frontend-dist
RUN chmod +x /app/docker-entrypoint.sh /app/worker-entrypoint.sh /app/setup-entrypoint.sh
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["/app/docker-entrypoint.sh"]
