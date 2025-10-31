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

# Expose port (if using API)
EXPOSE 8000

# Default command is left to docker-compose
