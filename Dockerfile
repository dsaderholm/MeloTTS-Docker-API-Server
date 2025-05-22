FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# First, let's try a more stable approach with specific compatible versions
# Install PyTorch 2.1.0 with Intel GPU support (more stable than nightly)
RUN pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Install Intel Extension for PyTorch with specific compatible version
RUN pip install intel-extension-for-pytorch==2.1.0

# Alternative: If the above fails, try the oneAPI approach
# RUN pip install torch torchvision torchaudio intel-extension-for-pytorch -f https://developer.intel.com/ipex-whl-stable-cpu

# Copy requirements and create a filtered version without conflicting packages
COPY requirements.txt .

# Create filtered requirements (remove conflicting packages)
RUN grep -v "^torch==" requirements.txt | \
    grep -v "^torchaudio==" | \
    grep -v "^nvidia-" | \
    grep -v "^tensorboard" > requirements_filtered.txt

# Install filtered requirements
RUN pip install -r requirements_filtered.txt

# Install compatible tensorboard
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