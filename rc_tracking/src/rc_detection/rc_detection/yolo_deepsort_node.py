#!/usr/bin/env python3
"""
YOLO + DeepSORT 객체 추적 노드
- YOLO로 객체 감지
- DeepSORT로 추적
- 색상 히스토그램 기반 재식별 (ID 변경 시 복구)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, Int32
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# 커스텀 메시지 import
try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError as e:
    print(f"❌ Detection 메시지 import 실패: {e}")
    from std_msgs.msg import String
    Detection = None
    DetectionArray = None


class YOLODeepSORTNode(Node):
    def __init__(self):
        super().__init__('yolo_deepsort_node')

        # ====================================================================
        # 파라미터 설정
        # ====================================================================
        self.declare_parameter('model_path', 'yolo26m.engine')
        self.declare_parameter('confidence_threshold', 0.6)
        self.declare_parameter('target_class', 'person')      # 추적할 대상 클래스
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('show_preview', True)

        # 락온 관련 파라미터
        self.declare_parameter('lock_frame_count', 30)        # 락온까지 필요한 프레임 수
        self.declare_parameter('similarity_threshold', 0.5)   # 색상 유사도 기준 (낮을수록 너그러움)
        self.declare_parameter('track_max_age', 15)           # 트랙 유지 시간 (프레임)
        self.declare_parameter('track_n_init', 3)             # 확정까지 필요한 연속 감지 수

        model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value
        self.target_class = self.get_parameter('target_class').value
        image_topic = self.get_parameter('image_topic').value
        self.show_preview = self.get_parameter('show_preview').value

        # 락온 파라미터 로드
        self.lock_frame_count = self.get_parameter('lock_frame_count').value
        self.similarity_threshold = self.get_parameter('similarity_threshold').value
        track_max_age = self.get_parameter('track_max_age').value
        track_n_init = self.get_parameter('track_n_init').value

        # ====================================================================
        # YOLO 모델 초기화
        # ====================================================================
        self.get_logger().info(f'YOLO 모델 로딩: {model_path}')
        self.yolo = YOLO(model_path)

        # ====================================================================
        # DeepSORT 트래커 초기화
        # ====================================================================
        self.tracker = DeepSort(
            max_age=track_max_age,          # 트랙 유지 시간
            n_init=track_n_init,            # 확정까지 필요한 연속 감지 수
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=None,
            embedder="torchreid",
            embedder_model_name="osnet_x1_0", # [중요] 모델명 지정
            half=True,
            embedder_gpu=True
        )

        # ====================================================================
        # 락온 및 재식별 관련 변수
        # ====================================================================
        self.target_hist = None             # 타겟 색상 히스토그램
        self.original_target_id = None      # 최초 락온 시 ID (화면 표시용, 변경 안됨)
        self.current_track_id = None        # 현재 추적 중인 DeepSORT ID (재식별 시 변경됨)
        self.is_locked = False              # 락온 상태
        self.lock_counter = 0               # 락온 카운터

        # CV Bridge
        self.bridge = CvBridge()

        # 거리 정보 (센서 퓨전용)
        self.latest_distance = None
        self.distance_timestamp = None

        # 가장 가까운 객체 ID
        self.closest_object_id = None

        # ====================================================================
        # ROS2 Subscriber 설정
        # ====================================================================
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )

        self.distance_sub = self.create_subscription(
            Float32,
            '/distance',
            self.distance_callback,
            10
        )

        self.closest_id_sub = self.create_subscription(
            Int32,
            '/closest_object_id',
            self.closest_id_callback,
            10
        )

        # ====================================================================
        # ROS2 Publisher 설정
        # ====================================================================
        if DetectionArray is not None:
            self.detection_pub = self.create_publisher(
                DetectionArray,
                '/detections',
                10
            )

        self.latest_frame = None

        self.get_logger().info('YOLO + DeepSORT 노드 초기화 완료')
        self.get_logger().info(f'추적 대상: {self.target_class}')

    def get_color_histogram(self, img_crop):
        """
        이미지에서 색상 히스토그램 추출 (재식별용)
        HSV 색공간에서 H, S 채널 사용
        """
        if img_crop is None or img_crop.size == 0:
            return None
        try:
            hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
            # bin 수 축소로 연산량 감소 (30, 32)
            hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            return hist
        except Exception:
            return None

    def distance_callback(self, msg):
        """거리 데이터 수신 콜백"""
        self.latest_distance = msg.data
        self.distance_timestamp = self.get_clock().now()

    def closest_id_callback(self, msg):
        """가장 가까운 객체 ID 수신 콜백"""
        self.closest_object_id = msg.data if msg.data >= 0 else None

    def image_callback(self, msg):
        """카메라 이미지 처리 콜백"""
        try:
            # ROS Image -> OpenCV 변환
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.latest_frame = cv_image.copy()

            height, width = cv_image.shape[:2]
            center_x, center_y = width // 2, height // 2

            # ========== [1단계] YOLO 추론 ==========
            results = self.yolo(cv_image, conf=self.conf_threshold, verbose=False)

            # DeepSORT 입력 포맷으로 변환 [x, y, w, h]
            detections_for_tracker = []

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = self.yolo.names[cls]

                    # 타겟 클래스 필터링
                    if self.target_class and class_name != self.target_class:
                        continue

                    w = x2 - x1
                    h = y2 - y1
                    detections_for_tracker.append((
                        [x1, y1, w, h],
                        conf,
                        class_name
                    ))

            # ========== [2단계] DeepSORT 추적 ==========
            tracks = self.tracker.update_tracks(
                detections_for_tracker,
                frame=cv_image
            )

            # ========== [3단계] 타겟 매칭 및 재식별 ==========
            best_match_track = None
            found_person_in_center = False

            for track in tracks:
                if not track.is_confirmed():
                    continue

                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)

                # 바운딩 박스 클램핑 (화면 밖 방지)
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(0, min(x2, width - 1))
                y2 = max(0, min(y2, height - 1))

                if x2 <= x1 or y2 <= y1:
                    continue

                # 색상 히스토그램 추출
                person_crop = cv_image[y1:y2, x1:x2]
                current_hist = self.get_color_histogram(person_crop)
                if current_hist is None:
                    continue

                # -------- [모드 A] 락온 대기 상태 --------
                if not self.is_locked:
                    # 바운딩 박스가 화면 중앙점을 포함하는지 체크
                    if (x1 < center_x < x2) and (y1 < center_y < y2):
                        found_person_in_center = True

                        # 카운터가 차면 락온 확정
                        if self.lock_counter >= self.lock_frame_count:
                            self.target_hist = current_hist.copy()
                            self.original_target_id = track.track_id
                            self.current_track_id = track.track_id
                            self.is_locked = True
                            self.get_logger().info(f'✅ 락온 완료! Target ID: {self.original_target_id}')

                # -------- [모드 B] 락온 후 추적 상태 --------
                else:
                    is_match = False

                    # 방법1: DeepSORT ID가 같으면 바로 매칭
                    if track.track_id == self.current_track_id:
                        is_match = True
                        # 타겟 히스토그램 점진적 업데이트 (조명 변화 대응)
                        cv2.accumulateWeighted(current_hist, self.target_hist, 0.1)
                        cv2.normalize(self.target_hist, self.target_hist, 0, 1, cv2.NORM_MINMAX)

                    # 방법2: ID가 다르면 색상 유사도로 재식별 시도
                    else:
                        similarity = cv2.compareHist(self.target_hist, current_hist, cv2.HISTCMP_CORREL)
                        if similarity > self.similarity_threshold:
                            is_match = True
                            old_id = self.current_track_id
                            self.current_track_id = track.track_id
                            self.get_logger().info(
                                f'🔄 재식별 성공! (원본 ID:{self.original_target_id} 유지, '
                                f'DeepSORT ID: {old_id} -> {self.current_track_id}, 유사도:{similarity:.2f})'
                            )

                    if is_match:
                        best_match_track = track
                        break

            # -------- 락온 카운터 관리 --------
            if not self.is_locked:
                if found_person_in_center:
                    self.lock_counter += 1
                else:
                    self.lock_counter = max(0, self.lock_counter - 2)  # 벗어나면 빠르게 감소

            # ========== [4단계] Detection 발행 ==========
            self.publish_detections(tracks, msg.header, best_match_track)

            # ========== [5단계] 시각화 ==========
            if self.show_preview:
                self.visualize(cv_image, tracks, best_match_track, center_x, center_y)

        except Exception as e:
            self.get_logger().error(f'이미지 콜백 에러: {str(e)}')

    def publish_detections(self, tracks, header, best_match_track):
        """추적된 객체 정보 발행"""
        if DetectionArray is None:
            self.get_logger().error('❌ DetectionArray가 None - 발행 불가')
            return

        detection_array = DetectionArray()
        detection_array.header = header

        confirmed_count = 0
        for track in tracks:
            if not track.is_confirmed():
                continue
            confirmed_count += 1

            track_id = track.track_id
            ltrb = track.to_ltrb()

            detection = Detection()

            # 락온된 타겟이면 원본 ID 사용 (일관성 유지)
            if self.is_locked and track_id == self.current_track_id:
                detection.track_id = int(self.original_target_id)
            else:
                detection.track_id = int(track_id)

            detection.class_name = track.get_det_class() if hasattr(track, 'get_det_class') else 'unknown'

            conf = track.get_det_conf() if hasattr(track, 'get_det_conf') else None
            detection.confidence = float(conf) if conf is not None else 0.0

            detection.x_min = int(ltrb[0])
            detection.y_min = int(ltrb[1])
            detection.x_max = int(ltrb[2])
            detection.y_max = int(ltrb[3])

            detection.center_x = float((ltrb[0] + ltrb[2]) / 2.0)
            detection.center_y = float((ltrb[1] + ltrb[3]) / 2.0)

            detection_array.detections.append(detection)

        self.detection_pub.publish(detection_array)

        # 상태 로깅
        if self.is_locked:
            status = f'🔒 LOCKED (ID:{self.original_target_id})'
            if best_match_track is None:
                status += ' - 타겟 탐색 중...'
        else:
            status = f'👀 SEARCHING ({self.lock_counter}/{self.lock_frame_count})'

        self.get_logger().info(
            f'{status} | Tracks:{len(tracks)}, Confirmed:{confirmed_count}',
            throttle_duration_sec=1.0
        )

    def visualize(self, image, tracks, best_match_track, center_x, center_y):
        """감지 결과 시각화"""
        vis_image = image.copy()

        # 거리 데이터 유효성 체크 (0.5초 이내)
        distance_valid = False
        if self.latest_distance is not None and self.distance_timestamp is not None:
            time_diff = (self.get_clock().now() - self.distance_timestamp).nanoseconds / 1e9
            distance_valid = time_diff < 0.5

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)

            # 락온된 타겟인지 확인
            is_target = (self.is_locked and track_id == self.current_track_id)

            if is_target:
                # 타겟: 초록색 굵은 박스
                box_color = (0, 255, 0)
                thickness = 3
                display_id = self.original_target_id
                label = f'[TARGET] ID:{display_id}'
            else:
                # 다른 객체: 노란색 얇은 박스
                box_color = (0, 255, 255)
                thickness = 2
                display_id = track_id
                label = f'ID:{display_id}'

            cv2.rectangle(vis_image, (x1, y1), (x2, y2), box_color, thickness)

            # 타겟에 거리 표시
            if is_target and distance_valid and self.latest_distance is not None:
                try:
                    dist_val = float(self.latest_distance)
                    label += f' | {dist_val:.2f}m'
                    cv2.putText(vis_image, f'{dist_val:.2f}m', (x1, y2 + 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                except (ValueError, TypeError):
                    pass

            cv2.putText(vis_image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

        # 락온 대기 중이면 중앙점 및 진행률 표시
        if not self.is_locked:
            cv2.circle(vis_image, (center_x, center_y), 8, (0, 0, 255), -1)
            progress_text = f'LOCK: {self.lock_counter}/{self.lock_frame_count}'
            cv2.putText(vis_image, progress_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # 락온 상태인데 타겟 못 찾으면 경고
        if self.is_locked and best_match_track is None:
            cv2.putText(vis_image, 'TARGET LOST!', (50, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        cv2.imshow('YOLO + DeepSORT Tracking', vis_image)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = YOLODeepSORTNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
