# MeloTTS Docker API Server with Intel Arc GPU Support

This is a modified version of the [original MeloTTS Docker API Server](https://github.com/timhagel/MeloTTS-Docker-API-Server) with added support for Intel Arc GPUs.

## Features

- Basic MeloTTS functionality through API calls
- Intel Arc GPU acceleration support
- Automatic fallback to CPU if GPU is not available

## Prerequisites

- Docker and Docker Compose
- Intel Arc GPU (e.g., A380) with drivers installed on the host system

## Building and Running

### Using Docker Compose (Recommended)

```bash
# Build and start the server with Intel GPU support
docker-compose -f docker-compose.intel.yml up -d

# Check logs to verify GPU detection
docker logs melotts-server
```

### Manual Docker Build and Run

```bash
# Build the image
docker build -t melotts-intel -f Dockerfile.intel .

# Run with GPU support
docker run --name melotts-server -p 8888:8080 \
  -e DEFAULT_SPEED=1 \
  -e DEFAULT_LANGUAGE=EN \
  -e DEFAULT_SPEAKER_ID=EN-Default \
  --device /dev/dri:/dev/dri \
  -v /dev/dri:/dev/dri \
  --restart unless-stopped \
  melotts-intel
```

## API Usage

The API usage is identical to the original MeloTTS Docker API Server:

### Basic Usage (Using Environment Defaults)

```bash
curl http://localhost:8888/convert/tts \
--header "Content-Type: application/json" \
-d '{ "text": "Put input here" }' \
--output "example.wav"
```

### Custom Parameters

```bash
curl http://localhost:8888/convert/tts \
--header "Content-Type: application/json" \
-d '{
  "text": "Put input here",
  "speed": "0.5",
  "language": "EN",
  "speaker_id": "EN-BR"
}' \
--output "example.wav"
```

## Supported Languages and Speakers

### Languages
- EN - English
- ES - Spanish
- FR - French
- ZH - Chinese
- JP - Japanese
- KR - Korean

### Speaker IDs (English)
- EN-US - American English accent
- EN-BR - British English accent
- EN_INDIA - Indian English accent
- EN-AU - Australian English accent
- EN-Default - Default English accent

## Troubleshooting

If the GPU is not being detected:

1. Verify the GPU is properly passed through to the Docker container:
   ```bash
   docker exec -it melotts-server ls -la /dev/dri
   ```

2. Check GPU driver status on the host:
   ```bash
   vainfo
   ```

3. Check if PyTorch can detect the Intel GPU:
   ```bash
   docker exec -it melotts-server python -c "import torch; import intel_extension_for_pytorch as ipex; print('GPU available:', torch.xpu.is_available() if hasattr(torch, 'xpu') else 'XPU module not available')"
   ```

## Acknowledgements

This is an enhanced version of the [MeloTTS Docker API Server](https://github.com/timhagel/MeloTTS-Docker-API-Server) with Intel GPU support.
The underlying TTS engine is [MeloTTS](https://github.com/myshell-ai/MeloTTS) from [MyShell](https://github.com/myshell-ai).