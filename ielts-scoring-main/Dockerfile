# File: ielts-scorer/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set timezone (optional)
ENV TZ=Asia/Ho_Chi_Minh

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip==24.0 \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

