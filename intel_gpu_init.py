import os
import torch
import logging

# Set up logging for GPU initialization
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_intel_arc_gpu():
    """Intel Arc GPU initialization for MeloTTS."""
    logger.info("🔍 Initializing Intel Arc GPU support for MeloTTS...")
    
    # Set Intel Arc optimization environment variables
    intel_env_vars = {
        "ONEAPI_DEVICE_SELECTOR": "level_zero:gpu",
        "INTEL_DEVICE_TYPE": "gpu", 
        "USE_IPEX": "1",
        "LIBVA_DRIVER_NAME": "iHD",
        "LIBVA_DRIVERS_PATH": "/usr/lib/x86_64-linux-gnu/dri",
        "ZE_AFFINITY_MASK": "0",  # Use first GPU if multiple present
        "INTEL_MEDIA_RUNTIME": "/usr/lib/x86_64-linux-gnu/dri",
    }
    
    # Apply environment variables
    for key, value in intel_env_vars.items():
        os.environ[key] = value
        logger.debug(f"Set {key}={value}")
    
    try:
        # Test Intel Extension for PyTorch
        try:
            import intel_extension_for_pytorch as ipex
            logger.info(f"📦 IPEX version: {ipex.__version__}")
            
            # Check Intel XPU availability
            if torch.xpu.is_available():
                device_count = torch.xpu.device_count()
                logger.info(f"🎮 Intel XPU devices available: {device_count}")
                
                for i in range(device_count):
                    device_props = torch.xpu.get_device_properties(i)
                    logger.info(f"   Device {i}: {device_props.name}")
                    logger.info(f"   Total Memory: {device_props.total_memory // (1024**2)} MB")
                    
                # Set default device to first XPU
                torch.xpu.set_device(0)
                logger.info(f"🎯 Default XPU device set to: xpu:0")
                return True
            else:
                logger.warning("❌ Intel XPU not available")
                return False
                
        except ImportError as e:
            logger.error(f"❌ Intel Extension for PyTorch not available: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing Intel Arc GPU: {str(e)}")
        return False

def get_optimal_device():
    """Get the optimal device for MeloTTS computations."""
    if initialize_intel_arc_gpu():
        return 'xpu:0'
    elif torch.cuda.is_available():
        return 'cuda:0'
    else:
        return 'cpu'

def optimize_model_for_intel_arc(model, device='xpu:0'):
    """Optimize MeloTTS model for Intel Arc GPU."""
    try:
        import intel_extension_for_pytorch as ipex
        
        # Move model to Intel Arc GPU
        model = model.to(device)
        
        # Apply Intel Arc optimizations
        model = ipex.optimize(model, dtype=torch.float16)
        logger.info(f"✅ MeloTTS model optimized for Intel Arc GPU: {device}")
        
        return model
    except Exception as e:
        logger.warning(f"⚠️ Intel Arc optimization failed: {e}")
        return model.to(device)

# Initialize on import
initialize_intel_arc_gpu()
