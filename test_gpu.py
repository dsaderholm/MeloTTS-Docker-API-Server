# MeloTTS Intel Arc GPU Test Script

import requests
import json
import time

def test_melotts_gpu():
    base_url = "http://localhost:8888"
    
    print("🧪 Testing MeloTTS Intel Arc GPU Setup")
    print("="*50)
    
    # Test 1: Health check
    print("1. Checking API health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ API is healthy")
            print(f"   📱 Device: {health_data['device']}")
            print(f"   🚀 Intel GPU: {health_data['intel_gpu_available']}")
            print(f"   📊 PyTorch: {health_data['torch_version']}")
            if health_data['intel_gpu_name']:
                print(f"   🎯 GPU Name: {health_data['intel_gpu_name']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Simple TTS request
    print("\n2. Testing TTS generation...")
    test_text = "Hello, this is a test of Intel Arc GPU acceleration with MeloTTS."
    
    payload = {
        "text": test_text,
        "speed": 1.0,
        "language": "EN",
        "speaker_id": "EN-Default"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/convert/tts",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        if response.status_code == 200:
            duration = end_time - start_time
            audio_size = len(response.content)
            print(f"   ✅ TTS generation successful")
            print(f"   ⏱️  Duration: {duration:.2f} seconds")
            print(f"   📦 Audio size: {audio_size} bytes")
            
            # Save test file
            with open("test_output.wav", "wb") as f:
                f.write(response.content)
            print(f"   💾 Audio saved as 'test_output.wav'")
            
        else:
            print(f"   ❌ TTS generation failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ TTS generation error: {e}")
        return False
    
    # Test 3: Performance test
    print("\n3. Running performance test...")
    test_texts = [
        "Short test.",
        "This is a medium length test sentence for performance evaluation.",
        "This is a longer test sentence that should take more time to process and will help us evaluate the performance characteristics of the Intel Arc GPU acceleration in MeloTTS."
    ]
    
    for i, text in enumerate(test_texts, 1):
        payload = {
            "text": text,
            "speed": 1.0,
            "language": "EN", 
            "speaker_id": "EN-Default"
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/convert/tts", json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                words = len(text.split())
                wps = words / duration if duration > 0 else 0
                print(f"   📝 Test {i}: {words} words in {duration:.2f}s ({wps:.1f} words/sec)")
            else:
                print(f"   ❌ Test {i} failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Test {i} error: {e}")
    
    print("\n🎉 Testing completed!")
    print("\nTo monitor GPU usage during testing, run:")
    print("   intel_gpu_top")
    
    return True

if __name__ == "__main__":
    test_melotts_gpu()
