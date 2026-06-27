FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD sh -c "python -c \"import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\\\"PORT\\\", \\\"8100\\\")}/health')\""
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8100}"]
