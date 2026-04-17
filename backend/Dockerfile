FROM python:3.11-slim

WORKDIR /app

# Install dependencies first — separate layer so it only reruns when requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# These directories are mounted as volumes at runtime — create them so Flask doesn't error
RUN mkdir -p knowledge_base chroma_db

EXPOSE 5000

CMD ["python", "app.py"]
