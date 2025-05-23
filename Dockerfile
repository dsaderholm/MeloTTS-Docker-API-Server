FROM python:3.10.14-slim

# Fix Debian 12 (Bookworm) to include non-free repositories
RUN sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources

# Install system dependencies and Intel Arc drivers
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    python3-pip python3-dev build-essential \
    intel-media-va-driver-non-free \
    vainfo intel-gpu-tools ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (now includes PyTorch 2.1.0 + IPEX)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

# Clone and install MeloTTS
RUN git clone https://github.com/myshell-ai/MeloTTS.git
WORKDIR /MeloTTS
RUN pip install --no-cache-dir -e .
RUN python -m unidic download

# Go back to app directory and copy application
WORKDIR /app
COPY . .

# Set Intel Arc environment variables
ENV LIBVA_DRIVER_NAME=iHD \
    LIBVA_DRIVERS_PATH=/usr/lib/x86_64-linux-gnu/dri \
    INTEL_MEDIA_RUNTIME=/usr/lib/x86_64-linux-gnu/dri

EXPOSE 8080
CMD ["python3", "app.py"]
