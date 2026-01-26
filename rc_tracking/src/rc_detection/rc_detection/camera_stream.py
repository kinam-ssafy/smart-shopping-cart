#!/usr/bin/env python3
from flask import Flask, Response
import cv2

app = Flask(__name__)

# 카메라 초기화 (0번 디바이스)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        # === 십자선 그리기 (정렬용) ===
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # 빨간색 십자선
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 0, 255), 2)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 0, 255), 2)
        
        # === 이미지를 JPG로 인코딩 ===
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # 브라우저로 전송 (MJPEG 스트리밍)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return "<h1>Camera Alignment Tool</h1><img src='/video_feed' width='640' height='480'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("="*50)
    print("🚀 웹캠 서버 실행 중!")
    print("💻 노트북 브라우저 주소창에 아래 주소를 입력하세요:")
    print("👉 http://<RC카_IP주소>:5000")
    print("="*50)
    # 0.0.0.0은 모든 외부 접속을 허용한다는 뜻입니다.
    app.run(host='0.0.0.0', port=5000, debug=False)