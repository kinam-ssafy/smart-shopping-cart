#!/usr/bin/env python3
"""
ROS Web Viewer
- 트래킹 노드가 발행하는 '/yolo_debug_image'를 받아서
- 웹 브라우저(Flask)로 쏴주는 중계기 역할을 합니다.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
from flask import Flask, Response

# ==========================================
# 1. Flask 웹 서버 설정
# ==========================================
app = Flask(__name__)
latest_frame = None
lock = threading.Lock()

def generate_frames():
    global latest_frame
    while True:
        with lock:
            if latest_frame is None:
                continue
            
            # 이미지를 JPG로 압축
            ret, buffer = cv2.imencode('.jpg', latest_frame)
            frame_bytes = buffer.tobytes()

        # 브라우저로 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return "<h1>RC Car Tracking View</h1><img src='/video_feed' style='width:100%; max-width:640px;'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ==========================================
# 2. ROS2 이미지 수신 노드 설정
# ==========================================
class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_subscriber')
        
        # YOLO가 발행하는 디버그 이미지를 구독
        self.subscription = self.create_subscription(
            Image,
            '/yolo_debug_image',  # yolo_deepsort_node.py에서 발행하는 토픽 이름
            self.listener_callback,
            10
        )
        self.bridge = CvBridge()
        self.get_logger().info('📺 웹 뷰어 대기 중... (/yolo_debug_image)')

    def listener_callback(self, msg):
        global latest_frame
        try:
            # ROS 이미지 -> OpenCV 이미지 변환
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # 전역 변수에 저장 (Flask가 가져갈 수 있게)
            with lock:
                latest_frame = cv_image
        except Exception as e:
            self.get_logger().error(f'이미지 변환 실패: {e}')

# ==========================================
# 3. 멀티스레딩 실행 (ROS + Flask)
# ==========================================
def run_ros_node():
    rclpy.init()
    node = ImageSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    # ROS2를 별도 스레드로 실행
    threading.Thread(target=run_ros_node, daemon=True).start()
    
    print("="*50)
    print("🚀 웹 뷰어 실행 됨!")
    print("💻 노트북 브라우저에서 접속하세요:")
    print("👉 http://<오린나노_IP>:5000")
    print("="*50)
    
    # 웹 서버 실행
    app.run(host='0.0.0.0', port=5000, debug=False)