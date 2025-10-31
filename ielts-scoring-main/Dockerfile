# File: ielts-scorer/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# ffmpeg is required for pydub
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The command to run the application will be provided by docker-compose