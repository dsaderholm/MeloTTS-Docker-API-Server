# MeloTTS with Intel Arc GPU Support
# Uses Intel's official IPEX-LLM base image for proven Arc GPU compatibility

FROM intelanalytics/ipex-llm-xpu:2.1.0-SNAPSHOT

# Set working directory
WORKDIR /app

# Install system dependencies needed for MeloTTS
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create filtered requirements without PyTorch conflicts
RUN grep -v "^torch" requirements.txt | \
    grep -v "^intel-extension-for-pytorch" | \
    grep -v "^tensorboard" > requirements_filtered.txt

# Install filtered requirements (PyTorch/IPEX already in base image)
RUN pip install --no-cache-dir -r requirements_filtered.txt

# Install compatible tensorboard
RUN pip install tensorboard

# Clone and install MeloTTS
RUN git clone https://github.com/myshell-ai/MeloTTS.git /tmp/MeloTTS
WORKDIR /tmp/MeloTTS
RUN pip install --no-cache-dir -e .
RUN python -m unidic download

# Return to app directory and copy application files
WORKDIR /app
COPY app.py .
COPY test_gpu.py .

# Create startup script
RUN echo '#!/bin/bash\n\
source /opt/intel/oneapi/setvars.sh --force\n\
source ipex-llm-init --gpu --device Arc\n\
export ONEAPI_DEVICE_SELECTOR=level_zero:0\n\
export ZE_AFFINITY_MASK=0\n\
export SYCL_CACHE_PERSISTENT=1\n\
echo "🚀 Starting MeloTTS with Intel Arc GPU support..."\n\
python app.py' > /app/start.sh && chmod +x /app/start.sh

# Set environment variables
ENV DEFAULT_SPEED=1.0
ENV DEFAULT_LANGUAGE=EN  
ENV DEFAULT_SPEAKER_ID=EN-Default
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["/app/start.sh"]