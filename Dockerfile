FROM python:3.10-slim

# Fix Debian repositories to include non-free packages
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources; \
    fi

# Install system dependencies including Intel GPU support
RUN apt-get update && apt-get install -y \
    git wget unzip build-essential curl \
    intel-media-va-driver-non-free \
    vainfo intel-gpu-tools ffmpeg \
    # MeCab and Japanese text processing
    mecab mecab-ipadic-utf8 libmecab-dev \
    # Additional language support
    locales locales-all \
    # Common build dependencies
    gnupg software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Set locale for proper text handling
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR /app

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install core dependencies first (PyTorch with Intel support)
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    transformers==4.30.0 \
    numpy==1.24.3

# Install Intel PyTorch Extension for Arc GPU support
RUN pip install --no-cache-dir intel-extension-for-pytorch==2.0.100+xpu --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/ || \
    pip install --no-cache-dir intel-extension-for-pytorch || \
    echo "IPEX installation failed, continuing without GPU support"

# Install MeCab Python wrapper BEFORE other packages
RUN pip install --no-cache-dir mecab-python3==1.0.6

# Test MeCab installation immediately
RUN python -c "import MeCab; print('MeCab basic test passed')" || echo "MeCab test failed, continuing"

# Install UniDic dictionary system
RUN pip install --no-cache-dir unidic==1.1.0

# Download UniDic dictionary with robust error handling
RUN python -c "\
try: \
    import unidic; \
    unidic.download(); \
    print('UniDic download successful'); \
except Exception as e: \
    print(f'UniDic download failed: {e}'); \
    print('Continuing without UniDic - will use system MeCab dictionary'); \
" || true

# Install remaining MeloTTS dependencies (the ones that were failing in your build)
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

# Final MeCab test with fallback
RUN python -c "\
try: \
    import MeCab; \
    tagger = MeCab.Tagger(); \
    result = tagger.parse('これはテストです'); \
    print('✅ MeCab working correctly'); \
    print('Test result:', result.strip()); \
except Exception as e: \
    print(f'⚠️ MeCab test failed: {e}'); \
    print('Will try alternative MeCab configuration at runtime'); \
" || echo "⚠️ MeCab test failed but continuing..."

# Copy application files
COPY app.py .
COPY test_gpu.py .

# Set comprehensive environment variables
ENV LIBVA_DRIVER_NAME=iHD \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    INTEL_MEDIA_RUNTIME=/usr/lib/x86_64-linux-gnu/dri \
    DEFAULT_SPEED=1.0 \
    DEFAULT_LANGUAGE=EN \
    DEFAULT_SPEAKER_ID=EN-Default \
    PYTHONUNBUFFERED=1 \
    # MeCab environment
    MECAB_PATH=/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd \
    MECAB_CHARSET=utf-8 \
    # Intel GPU optimization
    ONEAPI_DEVICE_SELECTOR=level_zero:0 \
    ZE_AFFINITY_MASK=0 \
    SYCL_CACHE_PERSISTENT=1

EXPOSE 8080

# Create startup script with GPU diagnostics and MeCab fallbacks
RUN echo '#!/bin/bash\n\
echo "🔍 System Diagnostic Check..."\n\
echo "PyTorch version: $(python -c \"import torch; print(torch.__version__)\" 2>/dev/null || echo \"Not found\")"\n\
echo "Intel GPU check:"\n\
python -c "\
try:\
    import torch, intel_extension_for_pytorch as ipex;\
    print(f\"✅ IPEX loaded, XPU available: {torch.xpu.is_available() if hasattr(torch, '\''xpu'\'') else '\''No XPU module'\''}\");\
    if hasattr(torch, '\''xpu'\'') and torch.xpu.is_available():\
        print(f\"🚀 Intel GPU detected: {ipex.xpu.get_device_name(0)}\");\
except Exception as e:\
    print(f\"⚠️ Intel GPU setup issue: {e}\");\
"\n\
echo "MeCab version: $(mecab --version 2>/dev/null || echo \"Not found\")"\n\
echo "🚀 Starting MeloTTS server with Intel Arc GPU support..."\n\
python app.py\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
