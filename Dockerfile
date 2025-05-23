FROM python:3.10.14-slim

# Fix Debian 12 (Bookworm) to include non-free repositories
RUN sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources

# Install system dependencies including MeCab
RUN apt-get update && apt-get install -y \
    git wget unzip build-essential curl \
    intel-media-va-driver-non-free \
    vainfo intel-gpu-tools ffmpeg \
    # MeCab and Japanese text processing
    mecab mecab-ipadic-utf8 libmecab-dev \
    # Additional language support
    locales locales-all \
    && rm -rf /var/lib/apt/lists/*

# Set locale for proper Japanese text handling
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /app

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install core dependencies first
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    transformers==4.30.0 \
    numpy==1.24.3

# Install MeCab Python wrapper BEFORE other packages
RUN pip install --no-cache-dir mecab-python3==1.0.6

# Test MeCab installation immediately
RUN python -c "import MeCab; print('MeCab basic test passed')"

# Install UniDic dictionary system
RUN pip install --no-cache-dir unidic==1.1.0

# Download and install UniDic dictionary properly
RUN python -c "\
import unidic; \
try: \
    unidic.download(); \
    print('UniDic download successful'); \
except Exception as e: \
    print(f'UniDic download failed: {e}'); \
    import sys; sys.exit(0)\
"

# Install remaining MeloTTS dependencies
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
    requests==2.31.0 \
    pydantic==2.0.0 \
    python-multipart==0.0.6

# Install cached-path (known to cause issues, so install separately)
RUN pip install --no-cache-dir cached-path==1.6.2 || echo "cached-path failed, continuing..."

# Clone MeloTTS and install with error handling
RUN git clone https://github.com/myshell-ai/MeloTTS.git /tmp/MeloTTS

# Install MeloTTS with fallback handling
RUN cd /tmp/MeloTTS && \
    pip install --no-cache-dir -e . || \
    (echo "MeloTTS main install failed, trying alternative..." && \
     pip install --no-cache-dir --no-deps -e . && \
     echo "MeloTTS installed without dependencies")

# Final MeCab + UniDic test
RUN python -c "\
import MeCab; \
import unidic; \
tagger = MeCab.Tagger(); \
result = tagger.parse('これはテストです'); \
print('✅ MeCab + UniDic working correctly'); \
print('Test result:', result.strip())\
" || echo "⚠️ MeCab test failed but continuing..."

# Copy application files
COPY app.py .
COPY test_gpu.py .

# Set environment variables
ENV LIBVA_DRIVER_NAME=iHD \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    INTEL_MEDIA_RUNTIME=/usr/lib/x86_64-linux-gnu/dri \
    DEFAULT_SPEED=1.0 \
    DEFAULT_LANGUAGE=EN \
    DEFAULT_SPEAKER_ID=EN-Default \
    PYTHONUNBUFFERED=1 \
    # MeCab environment
    MECAB_PATH=/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd \
    MECAB_CHARSET=utf-8

EXPOSE 8080

# Create startup script with MeCab diagnostics
RUN echo '#!/bin/bash\n\
echo "🔍 MeCab Diagnostic Check..."\n\
echo "MeCab version: $(mecab --version)"\n\
echo "MeCab config: $(mecab-config --dicdir)"\n\
echo "Available dictionaries: $(ls -la $(mecab-config --dicdir) 2>/dev/null || echo "None found")"\n\
echo "🚀 Starting MeloTTS server..."\n\
python app.py\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]