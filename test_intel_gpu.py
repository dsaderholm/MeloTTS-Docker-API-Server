#!/usr/bin/env python3
"""
Test Intel Arc GPU support for MeloTTS
"""

def test_intel_gpu():
    print("🔍 Testing Intel Arc GPU Support...")
    
    # Test 1: Check PyTorch version
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch not available")
        return False
    
    # Test 2: Check Intel Extension for PyTorch
    try:
        import intel_extension_for_pytorch as ipex
        print("✅ Intel Extension for PyTorch (IPEX) loaded")
        
        # Test 3: Check XPU availability
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            device_count = torch.xpu.device_count()
            print(f"✅ Intel XPU devices available: {device_count}")
            
            # Test 4: Get GPU name
            try:
                gpu_name = ipex.xpu.get_device_name(0)
                print(f"🚀 GPU: {gpu_name}")
            except:
                print("⚠️ Could not get GPU name")
                
            # Test 5: Simple tensor operation
            try:
                test_tensor = torch.tensor([1.0, 2.0, 3.0]).to("xpu")
                result = test_tensor * 2
                print(f"✅ GPU tensor operation successful: {result.cpu().tolist()}")
                return True
            except Exception as e:
                print(f"❌ GPU tensor operation failed: {e}")
                return False
        else:
            print("❌ Intel XPU not available")
            return False
            
    except ImportError:
        print("❌ Intel Extension for PyTorch not available")
        return False

if __name__ == "__main__":
    success = test_intel_gpu()
    
    if success:
        print("\n🎉 Intel Arc GPU support is working!")
        print("Your MeloTTS app should be able to use GPU acceleration.")
    else:
        print("\n⚠️ Intel Arc GPU support not working.")
        print("The app will run on CPU instead.")
    
    # Test MeloTTS import
    try:
        print("\n🔍 Testing MeloTTS import...")
        from melo.api import TTS
        print("✅ MeloTTS imported successfully")
    except Exception as e:
        print(f"❌ MeloTTS import failed: {e}")
