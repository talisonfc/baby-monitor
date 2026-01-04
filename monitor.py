import cv2
import pyaudio
import base64
import threading
import sys

from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'baby-monitor-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Camera Configuration
camera = cv2.VideoCapture(0)  # Use 0 for default camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FPS, 30)

arg1 = sys.argv[1]

# Audio Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
DEVICE_INDEX = int(arg1)

# PyAudio setup
p = pyaudio.PyAudio()
audio_stream = None
audio_streaming = False
audio_thread = None

def gen_frames():
    """Generate video frames for streaming"""
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Resize for faster streaming
            frame = cv2.resize(frame, (640, 480))
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Main page with video and audio player"""
    return render_template('index.html')

def stream_audio():
    """Stream audio data to connected clients"""
    global audio_streaming, audio_stream
    
    try:
        # Open audio stream
        audio_stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )
        
        print("Audio streaming started")
        
        while audio_streaming:
            try:
                # Read audio data
                data = audio_stream.read(CHUNK, exception_on_overflow=False)
                
                # Encode as base64 for transmission
                encoded_data = base64.b64encode(data).decode('utf-8')
                
                # Emit to all connected clients
                socketio.emit('audio_data', encoded_data, namespace='/')
                
            except Exception as e:
                print(f"Error reading audio: {e}")
                break
                
    except Exception as e:
        print(f"Error opening audio stream: {e}")
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        print("Audio streaming stopped")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected")

@socketio.on('start_audio')
def handle_start_audio():
    """Start audio streaming"""
    global audio_streaming, audio_thread
    
    if not audio_streaming:
        audio_streaming = True
        audio_thread = threading.Thread(target=stream_audio, daemon=True)
        audio_thread.start()
        print("Audio streaming requested by client")
        emit('audio_status', {'status': 'started'})

@socketio.on('stop_audio')
def handle_stop_audio():
    """Stop audio streaming"""
    global audio_streaming
    
    audio_streaming = False
    print("Audio streaming stopped by client")
    emit('audio_status', {'status': 'stopped'})

if __name__ == '__main__':
    print("=" * 50)
    print("Baby Monitor Server Starting")
    print("=" * 50)
    print(f"Access the monitor at: http://0.0.0.0:8080")
    print("Video and audio streaming enabled")
    print("=" * 50)
    
    try:
        # Run the server
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    finally:
        # Cleanup
        camera.release()
        p.terminate()
        print("\nServer stopped, resources released")