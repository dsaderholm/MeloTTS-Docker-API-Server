FROM python:3.10.14-slim

# Fix Debian 12 (Bookworm) to include non-free repositories
RUN sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git wget unzip build-essential \
    intel-media-va-driver-non-free \
    vainfo intel-gpu-tools ffmpeg \
    # MeCab dependencies for Japanese text processing
    mecab mecab-ipadic-utf8 libmecab-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and create a working version
COPY requirements.txt .

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install core dependencies first to avoid conflicts
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    transformers==4.30.0 \
    numpy==1.24.3

# Install MeloTTS specific packages with fixed versions
RUN pip install --no-cache-dir \
    fastapi==0.100.0 \
    uvicorn==0.23.0 \
    librosa==0.10.1 \
    jieba==0.42.1 \
    pypinyin==0.49.0 \
    cn2an==0.5.22 \
    gruut==2.2.3 \
    eng-to-ipa==0.0.2 \
    unidecode==1.3.7 \
    pydub==0.25.1 \
    mecab-python3==1.0.6

# Install remaining utilities
RUN pip install --no-cache-dir \
    requests==2.31.0 \
    pydantic==2.0.0 \
    python-multipart==0.0.6

# Clone and install MeloTTS with error handling
RUN git clone https://github.com/myshell-ai/MeloTTS.git /tmp/MeloTTS && \
    cd /tmp/MeloTTS && \
    sed -i 's/cached_path/#cached_path/' requirements.txt && \
    pip install --no-cache-dir -e . || true

# Install and configure UniDic dictionary for Japanese support
RUN pip install --no-cache-dir unidic-lite==1.0.8 && \
    python -c "import unidic; unidic.download()" || true

# Install cached-path separately to avoid conflicts
RUN pip install --no-cache-dir cached-path==1.6.2 || true

# Copy application files
COPY app.py .
COPY test_gpu.py .

# Set Intel Arc environment variables
ENV LIBVA_DRIVER_NAME=iHD \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    INTEL_MEDIA_RUNTIME=/usr/lib/x86_64-linux-gnu/dri \
    DEFAULT_SPEED=1.0 \
    DEFAULT_LANGUAGE=EN \
    DEFAULT_SPEAKER_ID=EN-Default \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "app.py"]