import cv2
import zmq
import numpy as np
from flask import Flask, Response

# ===========================
# ⚙️ 설정
# ===========================
ZMQ_VIDEO_PORT = 5556  # 비전 노드에서 이미지를 쏘는 포트

app = Flask(__name__)
context = zmq.Context()
socket = context.socket(zmq.SUB)
# 로컬호스트의 5556 포트 구독
socket.connect(f"tcp://localhost:{ZMQ_VIDEO_PORT}")
socket.setsockopt_string(zmq.SUBSCRIBE, '')

print(f"📺 영상 서버 대기 중... (Port: {ZMQ_VIDEO_PORT})")

def generate_stream():
    while True:
        try:
            # ZMQ로 JPEG 바이너리 수신
            jpg_bytes = socket.recv()
            
            # 웹 브라우저가 이해하는 형식으로 토스 (MJPEG)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')
        except Exception as e:
            print(f"Error: {e}")
            continue

@app.route('/')
def index():
    return "<h1>RC Car Video Stream</h1><img src='/video_feed' width='640' height='480'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # 웹 서버 실행 (접속은 http://젯슨IP:5000)
    # threaded=True를 써야 요청 처리가 빠름
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)