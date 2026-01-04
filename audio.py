import pyaudio
import sys

arg1 = sys.argv[1]

# Configurações comuns para microfones de câmera USB
FORMAT = pyaudio.paInt16
CHANNELS = 1          # A maioria das câmeras USB é mono
RATE = 44100          # Taxa de amostragem padrão
CHUNK = 1024          # Tamanho do buffer
DEVICE_INDEX = int(arg1)      # Substitua pelo índice encontrado no passo anterior

audio = pyaudio.PyAudio()

# Abrir o stream
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=DEVICE_INDEX,
                    frames_per_buffer=CHUNK)

print("Gravando...")
try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        # 'data' contém os bytes brutos do áudio para processamento
finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()
