# File: ielts-scorer/Dockerfile
FROM python:3.11-slim

WORKDIR /app
ENV TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip==24.0 && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway sẽ tự inject biến PORT khi khởi chạy
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
