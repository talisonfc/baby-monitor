import pyaudio

def get_webcam_mic_index(keywords=["USB", "Webcam", "Camera"]):
    p = pyaudio.PyAudio()
    device_index = None
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        # Verifica se o dispositivo é de entrada e contém palavras-chave
        if info.get('maxInputChannels') > 0:
            name = info.get('name')
            if any(key.lower() in name.lower() for key in keywords):
                print(f"[INFO] Webcam detectada: {name} no Índice {i}")
                device_index = i
                break
    
    p.terminate()
    return device_index

# Configuração automática dos parâmetros
MIC_INDEX = get_webcam_mic_index()

if MIC_INDEX is not None:
    PARAMS = {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 44100,
        "input_device_index": MIC_INDEX,
        "input": True,
        "frames_per_buffer": 1024
    }
    print(f"Parâmetros configurados para o índice {MIC_INDEX}")
else:
    print("Erro: Microfone da webcam não encontrado.")