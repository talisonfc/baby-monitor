import cv2
import pyaudio
import base64
import threading

from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'baby-monitor-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Camera Configuration
camera = cv2.VideoCapture(0)  # Use 0 for default camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FPS, 30)

# Audio Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# PyAudio setup
p = pyaudio.PyAudio()
audio_stream = None
audio_streaming = False
audio_thread = None

def get_default_input_device():
    """Get the default input device index"""
    try:
        default_device = p.get_default_input_device_info()
        device_index = default_device['index']
        device_name = default_device['name']
        print(f"Using audio device: {device_name} (index: {device_index})")
        return device_index
    except Exception as e:
        print(f"Error getting default input device: {e}")
        # Try to find any available input device
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                print(f"Using audio device: {info.get('name')} (index: {i})")
                return i
        return None

AUDIO_DEVICE_INDEX = get_default_input_device()

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
    
    if AUDIO_DEVICE_INDEX is None:
        print("Error: No audio input device available")
        socketio.emit('audio_error', {'error': 'No audio input device found'}, namespace='/')
        return
    
    try:
        # Open audio stream with the detected device
        audio_stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=AUDIO_DEVICE_INDEX,
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
        socketio.emit('audio_error', {'error': str(e)}, namespace='/')
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        print("Audio streaming stopped")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected - Session ID: {socketio.server.environ.get('REMOTE_ADDR', 'unknown')}")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected")

@socketio.on('test_event')
def handle_test():
    """Test event handler"""
    print("TEST EVENT RECEIVED!")
    emit('test_response', {'message': 'Test successful!'})

@socketio.on('start_audio')
def handle_start_audio():
    """Start audio streaming"""
    global audio_streaming, audio_thread
    print("=" * 50)
    print("RECEIVED START_AUDIO REQUEST")
    print("=" * 50)
    
    if not audio_streaming:
        audio_streaming = True
        
        # Wait for any existing thread to finish
        if audio_thread and audio_thread.is_alive():
            audio_streaming = False
            audio_thread.join(timeout=1)
            audio_streaming = True
        
        audio_thread = threading.Thread(target=stream_audio, daemon=True)
        audio_thread.start()
        print("Audio streaming thread started")
        emit('audio_status', {'status': 'started'})
    else:
        print("Audio streaming already active")
        emit('audio_status', {'status': 'already_started'})

@socketio.on('stop_audio')
def handle_stop_audio():
    """Stop audio streaming"""
    global audio_streaming
    print("Received stop_audio request")
    
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