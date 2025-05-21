FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Clone MeloTTS repository
RUN git clone https://github.com/myshell-ai/MeloTTS.git
WORKDIR /MeloTTS

# Install MeloTTS
RUN pip install --no-cache-dir -e .
RUN python -m unidic download

# Return to root and copy application files
WORKDIR /
COPY . .

EXPOSE 8080

CMD ["python", "app.py"]