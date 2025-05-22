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
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intel GPU support with comprehensive error handling
intel_gpu_available = False
intel_gpu_name = "Unknown"
ipex_loaded = False

def safe_gpu_init():
    """Safely initialize Intel GPU support with extensive error handling"""
    global intel_gpu_available, intel_gpu_name, ipex_loaded
    
    logger.info(f"🔍 PyTorch version: {torch.__version__}")
    
    # Step 1: Try to import Intel Extension for PyTorch
    try:
        import intel_extension_for_pytorch as ipex
        ipex_loaded = True
        logger.info("✅ Intel Extension for PyTorch imported successfully")
        
        # Step 2: Check for XPU availability
        try:
            if hasattr(torch, 'xpu'):
                logger.info("✅ torch.xpu module found")
                if torch.xpu.is_available():
                    intel_gpu_available = True
                    intel_gpu_name = ipex.xpu.get_device_name(0)
                    logger.info(f"🚀 Intel XPU device available: {intel_gpu_name}")
                    
                    # Step 3: Test basic GPU operations
                    try:
                        test_tensor = torch.tensor([1.0, 2.0, 3.0]).to('xpu')
                        logger.info("✅ Basic GPU tensor operations successful")
                        return True
                    except Exception as tensor_error:
                        logger.error(f"❌ GPU tensor operations failed: {tensor_error}")
                        intel_gpu_available = False
                        return False
                else:
                    logger.warning("⚠️ torch.xpu found but no XPU device available")
            else:
                logger.warning("⚠️ torch.xpu module not found in PyTorch")
        except Exception as xpu_error:
            logger.error(f"❌ XPU availability check failed: {xpu_error}")
            intel_gpu_available = False
            
    except ImportError as import_error:
        logger.warning(f"⚠️ Intel Extension for PyTorch not available: {import_error}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during GPU initialization: {e}")
    
    return False

# Initialize GPU support
gpu_success = safe_gpu_init()

load_dotenv()
DEFAULT_SPEED = float(os.getenv("DEFAULT_SPEED", 1.0))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "EN")
DEFAULT_SPEAKER_ID = os.getenv("DEFAULT_SPEAKER_ID", "EN-Default")

# Determine the best device to use
def get_optimal_device():
    if gpu_success and intel_gpu_available:
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
            
            # Create model with explicit device setting
            if device == "xpu":
                # Try GPU first
                try:
                    model = TTS(language=body.language, device="xpu")
                    logger.info(f"✅ TTS model created successfully for {body.language} on GPU")
                except Exception as gpu_error:
                    logger.warning(f"⚠️ GPU model creation failed: {gpu_error}")
                    logger.info("🔄 Falling back to CPU...")
                    model = TTS(language=body.language, device="cpu")
                    cache_key = f"{body.language}_cpu"  # Update cache key
                    logger.info(f"✅ TTS model created successfully for {body.language} on CPU (fallback)")
            else:
                model = TTS(language=body.language, device="cpu")
                logger.info(f"✅ TTS model created successfully for {body.language} on CPU")
            
            model_cache[cache_key] = model
            
        except Exception as e:
            logger.error(f"❌ Failed to create TTS model: {e}")
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
            
            # Generate speech with the model
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
        "intel_gpu_available": intel_gpu_available,
        "intel_gpu_name": intel_gpu_name if intel_gpu_available else None,
        "ipex_loaded": ipex_loaded,
        "torch_version": torch.__version__,
        "python_version": sys.version,
        "models_cached": len(model_cache),
        "gpu_init_success": gpu_success,
        "supported_languages": ["EN", "ES", "FR", "ZH", "JP", "KR"]
    }

@app.get("/")
async def root():
    return {
        "message": "MeloTTS API with Intel GPU Support",
        "device": device,
        "intel_gpu": intel_gpu_name if device == "xpu" else "Not used",
        "status": "GPU enabled" if gpu_success else "CPU only",
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
    print(f"🔧 IPEX Loaded: {ipex_loaded}")
    print(f"🖥️  Device: {device}")
    if device == "xpu":
        print(f"🚀 Intel GPU: {intel_gpu_name}")
        print("✨ GPU acceleration enabled!")
    else:
        print("💻 Running on CPU")
        if not gpu_success:
            print("⚠️  GPU initialization failed - check logs above")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
