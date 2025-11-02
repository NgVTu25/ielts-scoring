# File: Dockerfile

# ===== STAGE 1: Build Environment =====
FROM python:3.11-slim as builder

WORKDIR /app
ENV TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    python3-dev \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip==24.0 && \
    pip install --no-cache-dir --prefix="/install" \
    torch==2.1.0 torchaudio==2.1.0 torchvision==0.16.0 \
    --index-url https://download.pytorch.org/whl/cpu
# --------------------------------------------------

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt


# ===== STAGE 2: Final Image =====
FROM python:3.11-slim

WORKDIR /app
ENV TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]