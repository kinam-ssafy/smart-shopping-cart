#!/usr/bin/env python3
"""
YOLO + DeepSORT + Web Server 통합 노드
기능:
1. 웹 브라우저로 실시간 영상 송출 (Flask)
2. YOLOv8로 객체 탐지
3. DeepSORT로 객체 추적 (ID 부여)
4. 중앙 집중식 락온(Lock-on) 및 타겟 재탐색(Re-ID) 로직 포함
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

# 커스텀 메시지 import 시도 (없으면 무시)
try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError:
    Detection = None
    DetectionArray = None

# ==========================================
# 🌐 Flask 웹 서버 설정 (영상 스트리밍용)
# ==========================================
app = Flask(__name__)
output_frame = None  # 웹으로 송출할 프레임을 저장하는 전역 변수
lock = threading.Lock()  # 쓰레드 간 충돌 방지를 위한 락

def get_ip_address():
    """현재 기기의 IP 주소를 자동으로 가져옵니다 (접속 URL 안내용)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_frames():
    """웹 브라우저로 보낼 MJPEG 스트림 생성 제너레이터"""
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                time.sleep(0.01)
                continue
            # 이미지를 JPG로 압축 (압축률이 높을수록 빠르지만 화질 저하)
            ret, buffer = cv2.imencode('.jpg', output_frame)
            frame_bytes = buffer.tobytes()

        # 멀티파트 응답 포맷으로 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03) # 약 30fps 제한

@app.route('/')
def index():
    """메인 페이지: 영상 태그만 덩그러니 보여줌"""
    return "<h1>Smart Cart Tracking View</h1><img src='/video_feed' style='width:100%; max-width:640px;'>"

@app.route('/video_feed')
def video_feed():
    """실제 영상 데이터를 쏘아주는 라우트"""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask_server():
    """Flask 서버를 별도 쓰레드에서 실행"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # 불필요한 접속 로그 숨기기
    
    ip_addr = get_ip_address()
    print("\n" + "="*60)
    print(f"🚀 웹 뷰어 실행 됨! (Smart Cart Mode)")
    print(f"💻 노트북에서 접속: http://{ip_addr}:5000")
    print("="*60 + "\n")
    
    # host='0.0.0.0'은 외부 접속 허용을 의미
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


# ==========================================
# 🧠 YOLO + DeepSORT ROS 노드
# ==========================================
class YOLODeepSORTNode(Node):
    def __init__(self):
        super().__init__('yolo_deepsort_node')

        # ----------------------------------
        # 1. 파라미터 설정 (launch 파일에서 변경 가능)
        # ----------------------------------
        self.declare_parameter('model_path', 'yolo26s.engine')
        self.declare_parameter('confidence_threshold', 0.6)
        # self.declare_parameter('target_class', 'person')
        self.declare_parameter('target_class', 'teddy bear')
        
        # 락온/추적 관련 튜닝 파라미터
        self.declare_parameter('lock_frame_count', 45)       # 중앙에 몇 프레임 머물러야 락온할지
        self.declare_parameter('similarity_threshold', 0.7)  # 히스토그램 유사도 기준 (0~1)
        self.declare_parameter('track_max_age', 15)          # 화면에서 사라져도 몇 프레임까지 기억할지
        self.declare_parameter('track_n_init', 3)            # 몇 프레임 연속 탐지되어야 진짜로 인정할지

        # 파라미터 가져오기
        model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value
        self.target_class = self.get_parameter('target_class').value
        
        self.lock_frame_count = self.get_parameter('lock_frame_count').value
        self.similarity_threshold = self.get_parameter('similarity_threshold').value
        track_max_age = self.get_parameter('track_max_age').value
        track_n_init = self.get_parameter('track_n_init').value

        # ----------------------------------
        # 2. 모델 및 트래커 초기화
        # ----------------------------------
        self.get_logger().info(f'YOLO 모델 로딩: {model_path}')
        self.yolo = YOLO(model_path) # TensorRT 엔진 로드 권장

        self.tracker = DeepSort(
            max_age=track_max_age,
            n_init=track_n_init,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3, # 임베딩 벡터 거리 기준
            embedder="torchreid",
            embedder_model_name="osnet_x1_0", # 사람 재식별에 좋은 경량 모델
            half=True,           # FP16 사용 (속도 향상)
            embedder_gpu=True    # GPU 사용
        )

        # ----------------------------------
        # 3. 상태 변수 초기화
        # ----------------------------------
        self.target_hist = None         # 락온된 타겟의 색상 히스토그램 (ID 변경 시 재추적용)
        self.original_target_id = None  # 최초 락온 시의 ID (표시용)
        self.current_track_id = None    # 현재 추적 중인 DeepSORT ID
        self.is_locked = False          # 현재 락온 상태인지 여부
        self.lock_counter = 0           # 락온 카운트다운

        self.bridge = CvBridge()
        self.latest_distance = None     # 라이다/초음파 등에서 오는 거리 정보
        self.closest_object_id = None
        self.distance_timestamp = None

        # ----------------------------------
        # 4. ROS 통신 설정
        # ----------------------------------
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.create_subscription(Float32, '/distance', self.distance_callback, 10)
        self.create_subscription(Int32, '/closest_object_id', self.closest_id_callback, 10)

        if DetectionArray:
            self.detection_pub = self.create_publisher(DetectionArray, '/detections', 10)
        
        # 웹 서버 쓰레드 시작
        self.web_thread = threading.Thread(target=start_flask_server, daemon=True)
        self.web_thread.start()

    def distance_callback(self, msg):
        self.latest_distance = msg.data
        self.distance_timestamp = self.get_clock().now()

    def closest_id_callback(self, msg):
        self.closest_object_id = msg.data

    def get_color_histogram(self, img_crop):
        """이미지 영역의 색상 특징을 추출 (ID가 바뀔 때 동일인인지 판단하기 위함)"""
        if img_crop is None or img_crop.size == 0: return None
        hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
        # H(색상), S(채도)에 대해서만 히스토그램 계산 (V는 조명 영향이 커서 제외)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    def image_callback(self, msg):
        global output_frame
        try:
            # ROS 이미지를 OpenCV 포맷으로 변환
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            height, width = cv_image.shape[:2]
            center_x, center_y = width // 2, height // 2

            # 1. YOLO 객체 탐지 수행
            results = self.yolo(cv_image, conf=self.conf_threshold, verbose=False)
            detections_for_tracker = []
            
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = self.yolo.names[cls]
                    
                    # 설정한 타겟 클래스(예: person)만 추적
                    if self.target_class and class_name != self.target_class: continue
                    
                    # DeepSORT 입력 형식: [[x,y,w,h], conf, class]
                    detections_for_tracker.append(([x1, y1, x2-x1, y2-y1], conf, class_name))

            # 2. DeepSORT 트래커 업데이트
            tracks = self.tracker.update_tracks(detections_for_tracker, frame=cv_image)

            # -----------------------------------------------------------
            # 3. 트랙킹 데이터 후처리 (화면 밖, 깨진 박스 등 제거)
            # -----------------------------------------------------------
            track_current_obj = None # 현재 우리가 쫓고 있는 객체(가 있다면)
            candidate_tracks = []    # 화면에 있는 모든 후보 객체들
            
            for track in tracks:
                if not track.is_confirmed(): continue # 추적 확정된 객체만
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                # 좌표 예외처리
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)
                if x2 <= x1 or y2 <= y1: continue

                # 거리 계산을 위해 중심점 구하기
                obj_cx, obj_cy = (x1 + x2) / 2, (y1 + y2) / 2
                dist_to_center = np.sqrt((obj_cx - center_x)**2 + (obj_cy - center_y)**2)
                
                # 히스토그램 추출 (재식별용)
                person_crop = cv_image[y1:y2, x1:x2]
                hist = self.get_color_histogram(person_crop)
                
                if hist is not None:
                    candidate_tracks.append({
                        'track': track,
                        'hist': hist,
                        'dist_to_center': dist_to_center,
                        'box': (x1, y1, x2, y2)
                    })
                
                # 만약 지금 락온된 상태고, 이 트랙이 내 주인의 ID와 같다면?
                if self.is_locked and track.track_id == self.current_track_id:
                    track_current_obj = track

            # -----------------------------------------------------------
            # 4. 로직 분기: [A] 락온 시도 vs [B] 추적 유지
            # -----------------------------------------------------------
            best_match_track = None

            # [A] 아직 주인을 못 찾음 (Lock-on Phase)
            if not self.is_locked:
                closest_track_info = None
                min_dist = float('inf')

                # 화면 중앙에 있는 사람 찾기
                for item in candidate_tracks:
                    x1, y1, x2, y2 = item['box']
                    # 박스가 화면 정중앙을 포함하고 있는지 확인
                    if (x1 < center_x < x2) and (y1 < center_y < y2):
                        if item['dist_to_center'] < min_dist:
                            min_dist = item['dist_to_center']
                            closest_track_info = item
                
                # 중앙에 사람이 있으면 카운트 증가
                if closest_track_info:
                    self.lock_counter += 1
                    # 일정 시간(프레임) 이상 중앙에 머물면 락온 성공!
                    if self.lock_counter >= self.lock_frame_count:
                        self.target_hist = closest_track_info['hist'] # 옷 색깔 저장
                        self.original_target_id = closest_track_info['track'].track_id
                        self.current_track_id = closest_track_info['track'].track_id
                        self.is_locked = True
                        self.get_logger().info(f'✅ 락온 완료! ID:{self.original_target_id}')
                else:
                    # 중앙에서 벗어나면 카운트 감소 (바로 0이 되지 않고 천천히 줄어듦)
                    self.lock_counter = max(0, self.lock_counter - 1)

            # [B] 이미 주인이 있음 (Tracking Phase)
            else:
                # Case 1: ID가 그대로 유지되고 있음 (가장 좋음)
                if track_current_obj:
                    best_match_track = track_current_obj
                
                # Case 2: ID가 사라짐 (가림, 화면 밖 나갔다 들어옴, ID 스위칭 발생)
                # -> 저장해둔 옷 색깔(히스토그램)로 비슷한 사람 찾기
                else:
                    max_sim = 0.0
                    best_candidate = None
                    
                    for item in candidate_tracks:
                        # 히스토그램 유사도 비교 (Correlation)
                        sim = cv2.compareHist(self.target_hist, item['hist'], cv2.HISTCMP_CORREL)
                        if sim > max_sim:
                            max_sim = sim
                            best_candidate = item['track']
                    
                    # 유사도가 일정 수준 이상이면 "주인이 ID가 바뀌었구나"라고 판단
                    if best_candidate and max_sim > self.similarity_threshold:
                        # [핵심] ID가 실제로 바뀔 때만 로그 출력 (도배 방지)
                        if self.current_track_id != best_candidate.track_id:
                             self.get_logger().info(f'🔄 타겟 변경: ID {self.current_track_id} -> {best_candidate.track_id} (유사도: {max_sim:.2f})')
                        
                        # 추적 대상 ID 갱신
                        self.current_track_id = best_candidate.track_id
                        best_match_track = best_candidate

            # -----------------------------------------------------------
            # 5. 시각화(Drawing) 및 데이터 발행
            # -----------------------------------------------------------
            self.visualize(cv_image, tracks, best_match_track, center_x, center_y)
            
            # 웹 서버 송출용 변수 업데이트 (Thread Safe)
            with lock:
                output_frame = cv_image.copy()

            # 제어 노드 등으로 토픽 발행
            self.publish_detections(tracks, msg.header)

        except Exception as e:
            self.get_logger().error(f'YOLO 에러: {e}')

    def visualize(self, img, tracks, best_track, cx, cy):
        """화면에 박스와 텍스트를 그리는 함수"""
        dist_valid = False
        # 거리 센서 데이터가 최신인지 확인 (0.5초 이내)
        if self.latest_distance and self.distance_timestamp:
            if (self.get_clock().now() - self.distance_timestamp).nanoseconds / 1e9 < 0.5:
                dist_valid = True

        for track in tracks:
            if not track.is_confirmed(): continue
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            
            # 타겟인 경우 초록색, 아니면 노란색
            is_target = (self.is_locked and track.track_id == self.current_track_id)
            color = (0, 255, 0) if is_target else (0, 255, 255)
            thick = 3 if is_target else 2
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thick)
            
            label = f'ID:{track.track_id}'
            if is_target:
                label = f'TARGET (Orig:{self.original_target_id})'
                if dist_valid:
                    label += f' {self.latest_distance:.2f}m'
                
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # 락온 시도 중일 때 중앙 점과 카운트 표시
        if not self.is_locked:
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(img, f'LOCKING: {self.lock_counter}/{self.lock_frame_count}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        # 타겟을 놓쳤을 때 경고
        elif best_track is None:
            cv2.putText(img, 'TARGET LOST', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    def publish_detections(self, tracks, header):
        """탐지 결과를 ROS 토픽으로 발행"""
        if not DetectionArray: return
        msg = DetectionArray()
        msg.header = header
        for track in tracks:
            if not track.is_confirmed(): continue
            det = Detection()
            
            # 제어 노드가 헷갈리지 않게 ID를 관리
            # 현재 추적중인 타겟이라면 -> 원래 알던 ID(original)로 보내줌 (ID 스위칭 은폐)
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

