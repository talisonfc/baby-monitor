#!/usr/bin/env python3
"""Test script to verify audio device and streaming setup"""

import pyaudio
import sys

def list_audio_devices():
    """List all available audio devices"""
    p = pyaudio.PyAudio()
    
    print("=" * 60)
    print("Available Audio Devices:")
    print("=" * 60)
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"\nDevice {i}: {info.get('name')}")
        print(f"  Max Input Channels: {info.get('maxInputChannels')}")
        print(f"  Max Output Channels: {info.get('maxOutputChannels')}")
        print(f"  Default Sample Rate: {info.get('defaultSampleRate')}")
    
    print("\n" + "=" * 60)
    
    # Get default devices
    try:
        default_input = p.get_default_input_device_info()
        print(f"\nDefault Input Device: {default_input['name']} (index: {default_input['index']})")
    except:
        print("\nNo default input device found")
    
    try:
        default_output = p.get_default_output_device_info()
        print(f"Default Output Device: {default_output['name']} (index: {default_output['index']})")
    except:
        print("No default output device found")
    
    print("=" * 60)
    p.terminate()

def test_audio_recording(device_index=None, duration=3):
    """Test audio recording from specified device"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    try:
        print(f"\nTesting audio recording for {duration} seconds...")
        
        if device_index is None:
            device_index = p.get_default_input_device_info()['index']
        
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print(f"Recording from device {device_index}...")
        
        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            if i % 10 == 0:
                print(".", end="", flush=True)
        
        print("\n✓ Audio recording successful!")
        print(f"Captured {len(frames)} audio chunks")
        
        stream.stop_stream()
        stream.close()
        
    except Exception as e:
        print(f"\n✗ Error testing audio: {e}")
    finally:
        p.terminate()

if __name__ == "__main__":
    list_audio_devices()
    
    print("\n" + "=" * 60)
    print("Testing default audio input...")
    print("=" * 60)
    
    test_audio_recording(duration=3)
    
    print("\n" + "=" * 60)
    print("Audio test complete!")
    print("=" * 60)
