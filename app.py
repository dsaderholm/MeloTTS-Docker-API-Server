import os
import uvicorn
from fastapi import FastAPI, Body, Depends, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from melo.api import TTS
from dotenv import load_dotenv
import tempfile
import torch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intel GPU support
intel_gpu_available = False
intel_gpu_name = "Unknown"

try:
    import intel_extension_for_pytorch as ipex
    intel_gpu_available = True
    logger.info("✅ Intel Extension for PyTorch loaded successfully")
    
    # Check if XPU is actually available
    if torch.xpu.is_available():
        intel_gpu_name = ipex.xpu.get_device_name(0)
        logger.info(f"✅ Intel XPU device detected: {intel_gpu_name}")
    else:
        logger.warning("⚠️ Intel Extension for PyTorch loaded but XPU device not available")
        intel_gpu_available = False
        
except ImportError as e:
    logger.warning(f"⚠️ Intel Extension for PyTorch not available: {e}")
except Exception as e:
    logger.error(f"❌ Error initializing Intel GPU support: {e}")

load_dotenv()
DEFAULT_SPEED = float(os.getenv("DEFAULT_SPEED", 1.0))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "EN")
DEFAULT_SPEAKER_ID = os.getenv("DEFAULT_SPEAKER_ID", "EN-Default")

# Determine the best device to use
def get_optimal_device():
    if intel_gpu_available and torch.xpu.is_available():
        logger.info(f"🚀 Using Intel GPU: {intel_gpu_name}")
        return "xpu"
    else:
        logger.info("💻 Using CPU for inference")
        return "cpu"

device = get_optimal_device()

class TextModel(BaseModel):
    text: str
    speed: float = DEFAULT_SPEED
    language: str = DEFAULT_LANGUAGE
    speaker_id: str = DEFAULT_SPEAKER_ID

app = FastAPI(title="MeloTTS API with Intel GPU Support", version="1.0.0")

# Cache for TTS models to avoid reloading
model_cache = {}

def get_tts_model(body: TextModel):
    cache_key = f"{body.language}_{device}"
    
    if cache_key not in model_cache:
        try:
            logger.info(f"🔄 Creating TTS model for language: {body.language}, device: {device}")
            model = TTS(language=body.language, device=device)
            model_cache[cache_key] = model
            logger.info(f"✅ TTS model created successfully for {body.language}")
        except Exception as e:
            logger.error(f"❌ Failed to create TTS model: {e}")
            # Fallback to CPU if GPU fails
            if device == "xpu":
                logger.info("🔄 Falling back to CPU...")
                try:
                    model = TTS(language=body.language, device="cpu")
                    model_cache[f"{body.language}_cpu"] = model
                    logger.info("✅ CPU fallback successful")
                    return model
                except Exception as cpu_error:
                    logger.error(f"❌ CPU fallback also failed: {cpu_error}")
                    raise HTTPException(status_code=500, detail=f"Failed to initialize TTS model: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail=f"Failed to initialize TTS model: {str(e)}")
    
    return model_cache[cache_key]

@app.post("/convert/tts")
async def create_upload_file(
    body: TextModel = Body(...), model: TTS = Depends(get_tts_model)
):
    try:
        speaker_ids = model.hps.data.spk2id
        
        if body.speaker_id not in speaker_ids:
            available_speakers = list(speaker_ids.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Speaker ID '{body.speaker_id}' not available for language '{body.language}'. Available speakers: {available_speakers}"
            )

        logger.info(f"🎯 Processing TTS request: '{body.text[:50]}{'...' if len(body.text) > 50 else ''}' (device: {device})")

        # Use a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            output_path = tmp.name
            
            # Generate speech with the model (on GPU if available)
            model.tts_to_file(
                body.text, speaker_ids[body.speaker_id], output_path, speed=body.speed
            )

            logger.info(f"✅ TTS generation completed successfully")

            # Return the audio file
            response = FileResponse(
                output_path, 
                media_type="audio/wav", 
                filename=f"tts_output.wav",
                headers={"Content-Disposition": "attachment; filename=tts_output.wav"}
            )

        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error during TTS generation: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": device,
        "intel_gpu_available": intel_gpu_available and torch.xpu.is_available() if intel_gpu_available else False,
        "intel_gpu_name": intel_gpu_name if intel_gpu_available else None,
        "torch_version": torch.__version__,
        "models_cached": len(model_cache),
        "supported_languages": ["EN", "ES", "FR", "ZH", "JP", "KR"]
    }

@app.get("/")
async def root():
    return {
        "message": "MeloTTS API with Intel GPU Support",
        "device": device,
        "intel_gpu": intel_gpu_name if device == "xpu" else "Not used",
        "endpoints": {
            "POST /convert/tts": "Convert text to speech",
            "GET /health": "Check API health and GPU status",
        }
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎵 MeloTTS API Server with Intel Arc GPU Support")
    print("="*60)
    print(f"📊 PyTorch Version: {torch.__version__}")
    print(f"🖥️  Device: {device}")
    if device == "xpu":
        print(f"🚀 Intel GPU: {intel_gpu_name}")
        print("✨ GPU acceleration enabled!")
    else:
        print("💻 Running on CPU")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
