#!/usr/bin/env python3
"""
YOLO + DeepSORT + Web Server 통합 노드
- 스마트 쇼핑 카트 전용 로직 적용
- 초기 락온 시점의 색상 정보를 '절대 기준'으로 사용하여 재식별 수행
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
import socket

# 커스텀 메시지 import
try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError:
    Detection = None
    DetectionArray = None

# ==========================================
# 🌐 Flask 웹 서버 설정
# ==========================================
app = Flask(__name__)
output_frame = None
lock = threading.Lock()

def get_ip_address():
    """현재 기기의 IP 주소를 가져옵니다"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_frames():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                time.sleep(0.01)
                continue
            ret, buffer = cv2.imencode('.jpg', output_frame)
            frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    return "<h1>Smart Cart Tracking View</h1><img src='/video_feed' style='width:100%; max-width:640px;'>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask_server():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    ip_addr = get_ip_address()
    print("\n" + "="*60)
    print(f"🚀 웹 뷰어 실행 됨! (Smart Cart Mode)")
    print(f"💻 노트북에서 접속: http://{ip_addr}:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


# ==========================================
# 🧠 YOLO + DeepSORT ROS 노드
# ==========================================
class YOLODeepSORTNode(Node):
    def __init__(self):
        super().__init__('yolo_deepsort_node')

        # 파라미터 설정
        self.declare_parameter('model_path', 'yolo26m.engine')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('target_class', 'person')
        
        # 트래킹 관련 파라미터
        self.declare_parameter('lock_frame_count', 45)       # 락온에 필요한 프레임 수
        self.declare_parameter('similarity_threshold', 0.6)  # 재식별 유사도 기준 (0.5~0.7 추천)
        self.declare_parameter('track_max_age', 15)          # 놓쳤을 때 기억하는 시간
        self.declare_parameter('track_n_init', 2)

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

        # 락온 상태 변수
        self.target_hist = None         # [중요] 초기 락온된 색상 정보 (절대 불변)
        self.original_target_id = None  # 최초 ID (표시용)
        self.current_track_id = None    # 현재 추적 중인 DeepSORT ID (가변)
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

    def distance_callback(self, msg):
        self.latest_distance = msg.data
        self.distance_timestamp = self.get_clock().now()

    def closest_id_callback(self, msg):
        self.closest_object_id = msg.data

    def get_color_histogram(self, img_crop):
        """객체의 색상 히스토그램 추출 (HSV)"""
        if img_crop is None or img_crop.size == 0: return None
        hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
        # H(색상)와 S(채도)만 사용하여 조명 변화 영향 최소화
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

            # 2. DeepSORT 추적 업데이트
            tracks = self.tracker.update_tracks(detections_for_tracker, frame=cv_image)

            # 3. 락온 및 추적 로직
            best_match_track = None
            found_person_in_center = False

            for track in tracks:
                if not track.is_confirmed(): continue
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                
                # 좌표 클램핑
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)
                
                if x2 <= x1 or y2 <= y1: continue

                # 현재 객체의 색상 추출
                person_crop = cv_image[y1:y2, x1:x2]
                current_hist = self.get_color_histogram(person_crop)
                if current_hist is None: continue

                # [모드 1] 락온 전: 화면 중앙 탐색
                if not self.is_locked:
                    if (x1 < center_x < x2) and (y1 < center_y < y2):
                        found_person_in_center = True
                        # 카운터가 차면 락온 확정
                        if self.lock_counter >= self.lock_frame_count:
                            self.target_hist = current_hist  # ⭐ 현재 색상을 '기준'으로 저장
                            self.original_target_id = track.track_id
                            self.current_track_id = track.track_id
                            self.is_locked = True
                            self.get_logger().info(f'✅ 락온 완료! ID:{self.original_target_id}')
                
                # [모드 2] 락온 후: 추적 및 재식별
                else:
                    is_match = False
                    
                    # 2-1. DeepSORT ID가 같으면 -> 내 주인 맞음
                    if track.track_id == self.current_track_id:
                        is_match = True
                        # ⚠️ 중요: target_hist를 업데이트하지 않음! (초기 색상 유지)
                    
                    # 2-2. ID가 다르면 -> 색상 비교로 재식별 시도 (Re-ID)
                    else:
                        # 저장해둔 '초기 색상'과 '현재 객체 색상' 비교
                        sim = cv2.compareHist(self.target_hist, current_hist, cv2.HISTCMP_CORREL)
                        
                        # 유사도가 높으면 주인으로 다시 인정
                        if sim > self.similarity_threshold:
                            is_match = True
                            self.current_track_id = track.track_id # 새 ID로 갱신
                            self.get_logger().info(f'🔄 재식별 성공! ID:{track.track_id} (유사도: {sim:.2f})')
                    
                    if is_match:
                        best_match_track = track

            # 4. 락온 카운터 관리
            if not self.is_locked:
                if found_person_in_center: self.lock_counter += 1
                else: self.lock_counter = max(0, self.lock_counter - 2)

            # 5. 시각화 및 웹 송출
            self.visualize(cv_image, tracks, best_match_track, center_x, center_y)
            
            with lock:
                output_frame = cv_image.copy()

            # 6. 결과 발행 (컨트롤러용)
            self.publish_detections(tracks, msg.header)

        except Exception as e:
            self.get_logger().error(f'YOLO 처리 에러: {e}')

    def visualize(self, img, tracks, best_track, cx, cy):
        # 거리 데이터 유효성 체크 (0.5초 이내 데이터만 인정)
        dist_valid = False
        if self.latest_distance and self.distance_timestamp:
            if (self.get_clock().now() - self.distance_timestamp).nanoseconds / 1e9 < 0.5:
                dist_valid = True

        for track in tracks:
            if not track.is_confirmed(): continue
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            
            # 주인(추적 대상)은 초록색, 나머지는 노란색
            is_target = (self.is_locked and track.track_id == self.current_track_id)
            color = (0, 255, 0) if is_target else (0, 255, 255)
            thick = 3 if is_target else 2
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thick)
            
            # 라벨 표시
            label = f'ID:{track.track_id}'
            if is_target:
                label = f'TARGET (Orig:{self.original_target_id})'
                if dist_valid:
                    label += f' {self.latest_distance:.2f}m'
                
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # 락온 전 중앙 점 및 카운터 표시
        if not self.is_locked:
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(img, f'LOCKING: {self.lock_counter}/{self.lock_frame_count}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        # 놓쳤을 때 경고
        elif best_track is None:
            cv2.putText(img, 'TARGET LOST... SCANNING', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

    def publish_detections(self, tracks, header):
        if not DetectionArray: return
        msg = DetectionArray()
        msg.header = header
        for track in tracks:
            if not track.is_confirmed(): continue
            det = Detection()
            # 현재 추적 중인 대상이면 원본 ID로 위장해서 보냄 (컨트롤러 혼동 방지)
            if self.is_locked and track.track_id == self.current_track_id:
                det.track_id = int(self.original_target_id)
            else:
                det.track_id = int(track.track_id)
                
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