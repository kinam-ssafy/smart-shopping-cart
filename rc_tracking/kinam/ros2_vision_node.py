#!/usr/bin/env python3
"""
ROS2 Vision Node - YOLO + DeepSORT + Lock-on Logic
기존 vision_pub.py를 ROS2로 변환 (로직 95% 동일)
"""

import cv2
import numpy as np
import time
import torch
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool, Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# ====================================================================
# 🎛️ [USER CONFIG] 여기서 모든 수치를 조정하세요!
# ====================================================================

# 1. 👁️ 탐지 (YOLO) 관련
MODEL_FILE = '/home/ddari/Desktop/kinam/S14P11A401/rc_tracking/kinam/yolo26m.engine'
CONF_THRESHOLD = 0.5

# 2. 🎯 추적 (DeepSORT) 관련
TRACK_MAX_AGE = 10
TRACK_N_INIT = 5

# 3. 🔒 락온 (Lock-on) 로직
LOCK_FRAME_COUNT = 45
SIMILARITY_THRESHOLD = 0.5

# 4. 📷 하드웨어 설정
USB_CAM_ID = 0
SEND_IMG_QUALITY = 50

# ====================================================================
# ROS2 노드 클래스
# ====================================================================

class VisionNode(Node):
    def __init__(self):
        super().__init__('kinam_vision_node')

        # ROS2 퍼블리셔 생성
        self.pub_steer = self.create_publisher(Float32, '/kinam/steer', 10)
        self.pub_locked = self.create_publisher(Bool, '/kinam/locked', 10)
        self.pub_track_id = self.create_publisher(Int32, '/kinam/track_id', 10)
        self.pub_image = self.create_publisher(Image, '/kinam/image_raw', 10)

        self.bridge = CvBridge()

        self.get_logger().info('📡 ROS2 비전 노드 시작!')

        # 모델 로드
        if torch.cuda.is_available():
            self.get_logger().info(f'🚀 CUDA 감지됨! GPU({torch.cuda.get_device_name(0)}) 사용')
        else:
            self.get_logger().info('🚨 CUDA 감지 실패! CPU 모드 (느림)')

        self.model = YOLO(MODEL_FILE, task='detect')

        # DeepSORT 설정
        self.tracker = DeepSort(
            max_age=TRACK_MAX_AGE,
            n_init=TRACK_N_INIT,
            embedder='mobilenet',
            embedder_gpu=True,
            nms_max_overlap=1.0
        )

        # 카메라 초기화
        self.cap = self._init_camera()

        # 변수 초기화
        self.target_hist = None
        self.original_target_id = None
        self.current_track_id = None
        self.is_locked = False
        self.lock_counter = 0
        self.last_print_time = time.time()

    def _init_camera(self):
        """카메라 초기화 (기존 로직 그대로)"""
        # GStreamer 파이프라인
        def gstreamer_pipeline(sensor_id=0, capture_width=640, capture_height=480, framerate=30):
            return (
                "v4l2src device=/dev/video%d ! "
                "image/jpeg, width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
                "nvv4l2decoder mjpeg=1 ! "
                "nvvidconv ! "
                "video/x-raw, format=(string)BGRx ! "
                "appsink drop=1 sync=0"
                % (sensor_id, capture_width, capture_height, framerate)
            )

        # GStreamer 지원 체크
        def check_gstreamer_support():
            build_info = cv2.getBuildInformation()
            return "GStreamer:                   YES" in build_info

        if check_gstreamer_support():
            cap = cv2.VideoCapture(gstreamer_pipeline(sensor_id=USB_CAM_ID), cv2.CAP_GSTREAMER)
            if cap.isOpened():
                self.get_logger().info('✅ GStreamer 파이프라인 성공 (GPU 가속)')
            else:
                self.get_logger().warn('🚨 GStreamer 파이프라인 실패 -> V4L2 전환')
                cap = cv2.VideoCapture(USB_CAM_ID, cv2.CAP_V4L2)
        else:
            self.get_logger().warn('⚠️ OpenCV에 GStreamer 미지원 -> V4L2 사용')
            cap = cv2.VideoCapture(USB_CAM_ID, cv2.CAP_V4L2)

        if not cap.isOpened():
            self.get_logger().error('❌ 카메라 열기 실패!')
            raise RuntimeError('Camera failed to open')

        # V4L2 설정
        if cap.getBackendName() == "V4L2":
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.get_logger().info(f'📷 V4L2 설정: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} @ {cap.get(cv2.CAP_PROP_FPS)}fps')

        return cap

    def get_color_histogram(self, img_crop):
        """색상 히스토그램 계산 (기존 로직 그대로)"""
        if img_crop is None or img_crop.size == 0:
            return None
        try:
            hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            return hist
        except Exception:
            return None

    def run(self):
        """메인 루프 (기존 로직 거의 그대로)"""
        self.get_logger().info('🎥 영상 처리 시작...')

        while rclpy.ok():
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.001)
                continue

            # BGRx -> BGR 변환
            if frame.shape[2] == 4:
                frame = frame[:, :, :3]

            height, width, _ = frame.shape
            center_x, center_y = width // 2, height // 2

            # ========== [1단계] YOLO 추론 ==========
            results = self.model(frame, device=0, half=True, classes=[0], verbose=False)

            detections = []
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0].cpu().numpy())
                    if conf > CONF_THRESHOLD:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        detections.append(([x1, y1, x2-x1, y2-y1], conf, 0))

            # ========== [2단계] DeepSORT 추적 ==========
            tracks = self.tracker.update_tracks(detections, frame=frame)

            # ========== [3단계] 타겟 매칭 로직 ==========
            best_match_track = None
            best_match_box = None
            found_person_in_center = False

            # 기본값
            steer_val = 0.0
            locked_status = False
            track_id_val = -1

            for track in tracks:
                if not track.is_confirmed():
                    continue

                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)

                # 클램핑
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(0, min(x2, width - 1))
                y2 = max(0, min(y2, height - 1))

                if x2 <= x1 or y2 <= y1:
                    continue

                person_crop = frame[y1:y2, x1:x2]
                current_hist = self.get_color_histogram(person_crop)
                if current_hist is None:
                    continue

                # -------- [모드 A] 락온 대기 --------
                if not self.is_locked:
                    if (x1 < center_x < x2) and (y1 < center_y < y2):
                        found_person_in_center = True

                        # 노란 박스 + 진행률 바
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 3)
                        progress = self.lock_counter / LOCK_FRAME_COUNT
                        bar_w = int((x2 - x1) * progress)
                        cv2.rectangle(frame, (x1, y1-20), (x1 + bar_w, y1-10), (0, 255, 255), -1)

                        if self.lock_counter >= LOCK_FRAME_COUNT:
                            self.target_hist = current_hist
                            self.original_target_id = track.track_id
                            self.current_track_id = track.track_id
                            self.is_locked = True
                            self.get_logger().info(f'\n✅ 락온 완료! Target ID: {self.original_target_id}')

                # -------- [모드 B] 락온 후 추적 --------
                else:
                    is_match = False

                    # 방법1: DeepSORT ID 매칭
                    if track.track_id == self.current_track_id:
                        is_match = True
                        cv2.accumulateWeighted(current_hist, self.target_hist, 0.1)
                        cv2.normalize(self.target_hist, self.target_hist, 0, 1, cv2.NORM_MINMAX)

                    # 방법2: 색상 유사도 재식별
                    else:
                        similarity = cv2.compareHist(self.target_hist, current_hist, cv2.HISTCMP_CORREL)
                        if similarity > SIMILARITY_THRESHOLD:
                            is_match = True
                            self.current_track_id = track.track_id
                            self.get_logger().info(f'🔄 재식별 성공! (원본 ID:{self.original_target_id} 유지, DeepSORT ID:{self.current_track_id})')

                    if is_match:
                        best_match_track = track
                        best_match_box = (x1, y1, x2, y2)
                        break

            # ========== [4단계] 상태별 처리 & 조향값 계산 ==========

            # 락온 전: 카운터 관리
            if not self.is_locked:
                if found_person_in_center:
                    self.lock_counter += 1
                else:
                    self.lock_counter = max(0, self.lock_counter - 2)

                cv2.putText(frame, f"LOCK: {self.lock_counter}/{LOCK_FRAME_COUNT}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            # 락온 성공 + 타겟 발견
            if self.is_locked and best_match_track:
                bx1, by1, bx2, by2 = best_match_box
                target_cx = (bx1 + bx2) / 2

                # 조향값 계산
                steer_val = (target_cx - center_x) / (width / 2) * 34
                steer_val = max(-34, min(34, steer_val))

                locked_status = True
                track_id_val = self.original_target_id

                # 초록 박스
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 0), 3)
                cv2.putText(frame, f"ID:{self.original_target_id}", (bx1, by1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 락온 상태인데 타겟 못 찾음
            elif self.is_locked and not best_match_track:
                cv2.putText(frame, "LOST TARGET!", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            # ========== [5단계] ROS2 토픽 발행 ==========
            msg_steer = Float32()
            msg_steer.data = float(steer_val)
            self.pub_steer.publish(msg_steer)

            msg_locked = Bool()
            msg_locked.data = locked_status
            self.pub_locked.publish(msg_locked)

            msg_track_id = Int32()
            msg_track_id.data = track_id_val
            self.pub_track_id.publish(msg_track_id)

            # 영상 발행 (선택)
            try:
                img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
                self.pub_image.publish(img_msg)
            except Exception as e:
                self.get_logger().warn(f'영상 발행 실패: {e}')

            # 로그
            if time.time() - self.last_print_time > 1.0:
                if self.is_locked:
                    status_msg = f"🔒 LOCKED (ID:{self.original_target_id}) - Steer:{int(steer_val)}"
                else:
                    status_msg = f"👀 SEARCHING... ({self.lock_counter}/{LOCK_FRAME_COUNT})"

                self.get_logger().info(f'[RUNNING] {status_msg}')
                self.last_print_time = time.time()

    def cleanup(self):
        """종료 처리"""
        if self.cap:
            self.cap.release()
        self.get_logger().info('✅ 비전 노드 종료')


def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()

    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().info('🛑 종료 요청')
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
