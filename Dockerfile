FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with Intel GPU support first (this must come before other requirements)
RUN pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/xpu

# Install Intel Extension for PyTorch for GPU acceleration
RUN pip install intel-extension-for-pytorch

# Copy requirements and create a filtered version without conflicting packages
COPY requirements.txt .

# Create filtered requirements (remove conflicting packages)
RUN grep -v "^torch==" requirements.txt | \
    grep -v "^torchaudio==" | \
    grep -v "^nvidia-" | \
    grep -v "^tensorboard" > requirements_filtered.txt

# Install filtered requirements
RUN pip install -r requirements_filtered.txt

# Install tensorboard separately (compatible version)
RUN pip install tensorboard

# Clone and install MeloTTS
RUN git clone https://github.com/myshell-ai/MeloTTS.git
WORKDIR /MeloTTS
RUN pip install --no-cache-dir -e .
RUN python -m unidic download

# Return to root and copy application files
WORKDIR /
COPY . .

EXPOSE 8080
CMD ["python", "app.py"]