#!/usr/bin/env python3
"""
YOLO + DeepSORT + Web Server 통합 노드
- YOLO 추론 및 DeepSORT 추적 수행
- 별도의 뷰어 노드 없이 직접 Flask로 영상 송출 (포트 5000)
- ROS2 통신 부하를 줄여서 화면 끊김 해결
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, Int32
from cv_bridge import CvBridge
import cv2
import numpy as np
import threading
from flask import Flask, Response
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time

# 커스텀 메시지 import
try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError:
    Detection = None
    DetectionArray = None

# ==========================================
# 🌐 Flask 웹 서버 설정 (YOLO 노드 내장)
# ==========================================
app = Flask(__name__)
output_frame = None
lock = threading.Lock()

def generate_frames():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            # 이미지를 바로 JPEG로 압축해서 전송 (ZMQ 방식과 동일한 효율)
            ret, buffer = cv2.imencode('.jpg', output_frame)
            frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03) # CPU 과부하 방지

@app.route('/')
def index():
    return "<h1>YOLO Tracking View</h1><img src='/video_feed' style='width:100%; max-width:640px;'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask_server():
    # 로그 끄기 (터미널 깨끗하게)
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    # 서버 실행 (0.0.0.0으로 열어서 외부 접속 허용)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


# ==========================================
# 🧠 YOLO + DeepSORT ROS 노드
# ==========================================
class YOLODeepSORTNode(Node):
    def __init__(self):
        super().__init__('yolo_deepsort_node')

        # 파라미터
        self.declare_parameter('model_path', 'yolo26m.engine')
        self.declare_parameter('confidence_threshold', 0.6)
        self.declare_parameter('target_class', 'person')
        
        # 락온 파라미터
        self.declare_parameter('lock_frame_count', 45)
        self.declare_parameter('similarity_threshold', 0.6)
        self.declare_parameter('track_max_age', 15)
        self.declare_parameter('track_n_init', 3)

        model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value
        self.target_class = self.get_parameter('target_class').value
        
        self.lock_frame_count = self.get_parameter('lock_frame_count').value
        self.similarity_threshold = self.get_parameter('similarity_threshold').value
        track_max_age = self.get_parameter('track_max_age').value
        track_n_init = self.get_parameter('track_n_init').value

        # YOLO 모델 로딩
        self.get_logger().info(f'YOLO 모델 로딩: {model_path}')
        self.yolo = YOLO(model_path)

        # DeepSORT 초기화
        self.tracker = DeepSort(
            max_age=track_max_age,
            n_init=track_n_init,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            embedder="torchreid",
            embedder_model_name="osnet_x1_0",
            half=True,
            embedder_gpu=True
        )

        # 상태 변수
        self.target_hist = None
        self.original_target_id = None
        self.current_track_id = None
        self.is_locked = False
        self.lock_counter = 0

        self.bridge = CvBridge()
        self.latest_distance = None
        self.closest_object_id = None
        self.distance_timestamp = None

        # Subscribers
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.create_subscription(Float32, '/distance', self.distance_callback, 10)
        self.create_subscription(Int32, '/closest_object_id', self.closest_id_callback, 10)

        # Publishers
        if DetectionArray:
            self.detection_pub = self.create_publisher(DetectionArray, '/detections', 10)
        
        # 웹 서버 스레드 시작
        self.web_thread = threading.Thread(target=start_flask_server, daemon=True)
        self.web_thread.start()
        self.get_logger().info('🚀 웹 서버가 내장되었습니다! http://<IP>:5000 접속하세요.')

    def distance_callback(self, msg):
        self.latest_distance = msg.data
        self.distance_timestamp = self.get_clock().now()

    def closest_id_callback(self, msg):
        self.closest_object_id = msg.data

    def get_color_histogram(self, img_crop):
        if img_crop is None or img_crop.size == 0: return None
        hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    def image_callback(self, msg):
        global output_frame
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            height, width = cv_image.shape[:2]
            center_x, center_y = width // 2, height // 2

            # 1. YOLO 추론
            results = self.yolo(cv_image, conf=self.conf_threshold, verbose=False)
            detections_for_tracker = []
            
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = self.yolo.names[cls]
                    
                    if self.target_class and class_name != self.target_class:
                        continue
                        
                    detections_for_tracker.append(([x1, y1, x2-x1, y2-y1], conf, class_name))

            # 2. DeepSORT 업데이트
            tracks = self.tracker.update_tracks(detections_for_tracker, frame=cv_image)

            # 3. 락온 로직
            best_match_track = None
            found_person_in_center = False

            for track in tracks:
                if not track.is_confirmed(): continue
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                
                # 범위 체크
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)
                
                if x2 <= x1 or y2 <= y1: continue

                # 히스토그램 추출
                person_crop = cv_image[y1:y2, x1:x2]
                current_hist = self.get_color_histogram(person_crop)
                if current_hist is None: continue

                if not self.is_locked:
                    # 락온 대기
                    if (x1 < center_x < x2) and (y1 < center_y < y2):
                        found_person_in_center = True
                        if self.lock_counter >= self.lock_frame_count:
                            self.target_hist = current_hist
                            self.original_target_id = track.track_id
                            self.current_track_id = track.track_id
                            self.is_locked = True
                            self.get_logger().info(f'✅ 락온! ID:{self.original_target_id}')
                else:
                    # 락온 추적 (ID 매칭 or 재식별)
                    is_match = False
                    if track.track_id == self.current_track_id:
                        is_match = True
                        cv2.accumulateWeighted(current_hist, self.target_hist, 0.1)
                        cv2.normalize(self.target_hist, self.target_hist, 0, 1, cv2.NORM_MINMAX)
                    else:
                        sim = cv2.compareHist(self.target_hist, current_hist, cv2.HISTCMP_CORREL)
                        if sim > self.similarity_threshold:
                            is_match = True
                            self.current_track_id = track.track_id
                    
                    if is_match:
                        best_match_track = track

            # 카운터 관리
            if not self.is_locked:
                if found_person_in_center: self.lock_counter += 1
                else: self.lock_counter = max(0, self.lock_counter - 2)

            # 4. 시각화 및 웹 송출용 이미지 업데이트
            self.visualize(cv_image, tracks, best_match_track, center_x, center_y)
            
            # [핵심] Flask가 가져갈 수 있게 전역 변수에 저장
            with lock:
                output_frame = cv_image.copy()

            # 5. Detection 결과 발행 (제어 노드용)
            self.publish_detections(tracks, msg.header)

        except Exception as e:
            self.get_logger().error(f'YOLO 에러: {e}')

    def visualize(self, img, tracks, best_track, cx, cy):
        # 거리 유효성 체크
        dist_valid = False
        if self.latest_distance and self.distance_timestamp:
            if (self.get_clock().now() - self.distance_timestamp).nanoseconds / 1e9 < 0.5:
                dist_valid = True

        for track in tracks:
            if not track.is_confirmed(): continue
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            
            is_target = (self.is_locked and track.track_id == self.current_track_id)
            color = (0, 255, 0) if is_target else (0, 255, 255)
            thick = 3 if is_target else 2
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thick)
            
            label = f'ID:{self.original_target_id if is_target else track.track_id}'
            if is_target and dist_valid:
                label += f' {self.latest_distance:.2f}m'
                
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if not self.is_locked:
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(img, f'LOCK: {self.lock_counter}/{self.lock_frame_count}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif best_track is None:
            cv2.putText(img, 'TARGET LOST', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    def publish_detections(self, tracks, header):
        if not DetectionArray: return
        msg = DetectionArray()
        msg.header = header
        for track in tracks:
            if not track.is_confirmed(): continue
            det = Detection()
            det.track_id = int(self.original_target_id if (self.is_locked and track.track_id == self.current_track_id) else track.track_id)
            det.class_name = 'person'
            ltrb = track.to_ltrb()
            det.x_min, det.y_min, det.x_max, det.y_max = map(int, ltrb)
            det.center_x = (det.x_min + det.x_max) / 2.0
            det.center_y = (det.y_min + det.y_max) / 2.0
            msg.detections.append(det)
        self.detection_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = YOLODeepSORTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()