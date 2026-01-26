#!/usr/bin/env python3
"""
Distance LiDAR Node - Python SDK 사용
YDLiDAR Python SDK를 직접 사용하여 실시간 거리 측정
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import math
import threading
import time
import sys

try:
    import ydlidar
    YDLIDAR_AVAILABLE = True
except ImportError:
    print("❌ ydlidar 모듈 없음")
    YDLIDAR_AVAILABLE = False
    sys.exit(1)

try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError as e:
    print(f"❌ Detection 메시지 import 실패: {e}")
    DetectionArray = None


class DistanceLidarNode(Node):
    def __init__(self):
        super().__init__('distance_lidar_node')
        
        # LiDAR 데이터 저장
        self.latest_scan = None
        self.latest_detections = None
        self.scan_lock = threading.Lock()
        
        # 카메라 파라미터
        self.image_width = 640
        self.image_height = 480
        self.camera_fov = 60.0  # degrees
        
        # YDLiDAR 초기화
        self.laser = None
        self.lidar_thread = None
        self.running = False
        
        if not self.init_lidar():
            self.get_logger().error('LiDAR 초기화 실패')
            raise RuntimeError('LiDAR initialization failed')
        
        # ROS2 Subscribers
        if DetectionArray is not None:
            self.detection_sub = self.create_subscription(
                DetectionArray,
                '/detections',
                self.detection_callback,
                10
            )
        
        # Publisher
        self.closest_id_pub = self.create_publisher(
            Int32,
            '/closest_object_id',
            10
        )
        
        # Timer
        self.timer = self.create_timer(0.5, self.print_distance)
        
        self.get_logger().info('Distance LiDAR Node Started (Python SDK)')
        self.get_logger().info('=' * 60)

        self.declare_parameter('lidar_camera_offset', 0.0)
        self.lidar_offset_deg = self.get_parameter('lidar_camera_offset').value

        self.get_logger().info(f'🛠️ LiDAR 오차 보정값: {self.lidar_offset_deg}도')

    
    def init_lidar(self):
        """YDLiDAR Python SDK 초기화"""
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()
            
            # 포트 설정 - ttyUSB0 우선 선택
            port = "/dev/ttyUSB0"
            
            self.get_logger().info(f'LiDAR 포트: {port}')
            
            # LiDAR 설정 (S2PRO)
            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 6.0)
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 4)
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)
            
            # 초기화
            ret = self.laser.initialize()
            if not ret:
                self.get_logger().error('LiDAR initialize() 실패')
                return False
            
            # 스캔 시작
            ret = self.laser.turnOn()
            if not ret:
                self.get_logger().error('LiDAR turnOn() 실패')
                return False
            
            self.get_logger().info('✅ LiDAR 초기화 성공')
            
            # 스캔 스레드 시작
            self.running = True
            self.lidar_thread = threading.Thread(target=self.lidar_scan_loop, daemon=True)
            self.lidar_thread.start()
            
            return True
            
        except Exception as e:
            self.get_logger().error(f'LiDAR 초기화 예외: {e}')
            return False
    
    def lidar_scan_loop(self):
        """LiDAR 스캔 루프 (별도 스레드) + 캘리브레이션 디버그 추가"""
        scan = ydlidar.LaserScan()
        error_count = 0
        max_errors = 10
        
        # [추가] 출력 조절용 카운터 (너무 빠른 출력 방지)
        print_counter = 0
        
        while self.running and ydlidar.os_isOk():
            try:
                r = self.laser.doProcessSimple(scan)
                if r:
                    # 스캔 데이터를 저장
                    with self.scan_lock:
                        # ranges와 angles 추출
                        ranges = [p.range for p in scan.points]
                        angles = [p.angle for p in scan.points]
                        
                        # ==========================================
                        # [추가] 캘리브레이션용 디버그 코드 시작
                        # ==========================================
                        # 0.1m 이상인 유효한 데이터만 필터링 (너무 가까운 노이즈 제외)
                        valid_data = [(r, a) for r, a in zip(ranges, angles) if r > 0.1]
                        
                        if valid_data:
                            print_counter += 1
                            # 약 20프레임마다 한 번씩 출력 (로그 홍수 방지, 약 3초 간격)
                            if print_counter % 20 == 0:
                                # 거리가 가장 가까운 점 찾기 (거리 기준 최소값)
                                min_dist, min_angle = min(valid_data, key=lambda x: x[0])
                                min_angle_deg = math.degrees(min_angle)
                                
                                print(f"\n📏 [캘리브레이션 확인]")
                                print(f"   - 가장 가까운 물체 거리 : {min_dist:.3f}m")
                                print(f"   - 라이다가 인식한 각도 : {min_angle_deg:+.2f}도")
                                print(f"   👉 물체를 카메라 정중앙에 두고, 위 '각도' 값을 오차 보정값으로 쓰세요.\n")
                        # ==========================================
                        # [추가] 캘리브레이션용 디버그 코드 끝
                        # ==========================================
                        
                        self.latest_scan = {
                            'ranges': ranges,
                            'angles': angles,
                            'stamp': time.time()
                        }
                    error_count = 0  # 성공 시 에러 카운트 리셋
                else:
                    time.sleep(0.01)
            except Exception as e:
                error_count += 1
                if error_count < max_errors:
                    self.get_logger().error(f'스캔 에러 ({error_count}/{max_errors}): {e}')
                    time.sleep(0.1)
                else:
                    self.get_logger().error(f'스캔 에러 한계 도달 - 스레드 종료')
                    self.running = False
                    break
    
    def detection_callback(self, msg):
        """객체 감지 데이터 수신"""
        self.latest_detections = msg.detections
    
    def get_distance_from_lidar(self, center_x, bbox_width, track_id=None):
        """
        바운딩 박스 중심점에 해당하는 LiDAR 거리 계산
        """
        with self.scan_lock:
            if self.latest_scan is None:
                return None
            
            scan_data = self.latest_scan
        
        # 이미지 중심에서의 픽셀 오프셋
        pixel_offset = center_x - (self.image_width / 2.0)
        
        # 픽셀을 각도로 변환
        angle_per_pixel = self.camera_fov / self.image_width
        angle_offset = pixel_offset * angle_per_pixel
        # target_angle = math.radians(angle_offset)

        # [수정] 2. 오차값 적용
        # 카메라 각도 + 오차값 = 실제 라이다 각도
        final_angle_deg = angle_offset + self.lidar_offset_deg
        target_angle = math.radians(final_angle_deg)
        
        # 가장 가까운 LiDAR 포인트 찾기
        ranges = scan_data['ranges']
        angles = scan_data['angles']
        
        if len(ranges) == 0:
            return None
        
        # target_angle에 가장 가까운 인덱스 찾기
        min_diff = float('inf')
        best_idx = 0
        
        for i, angle in enumerate(angles):
            diff = abs(angle - target_angle)
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        
        # ±10도 윈도우 내의 평균 계산
        window_angle = math.radians(10)
        valid_ranges = []
        window_data = []  # 디버그용: 거리가 0보다 큰 데이터만
        
        for i, angle in enumerate(angles):
            if abs(angle - target_angle) < window_angle:
                r = ranges[i]
                angle_deg = math.degrees(angle)
                if r > 0:  # 거리가 0보다 큰 데이터만 저장
                    window_data.append((angle_deg, r))
                if 0.1 < r < 10.0:  # 유효 범위
                    valid_ranges.append(r)
        
        # 디버그 출력
        if track_id is not None:
            print(f"\n{'='*60}")
            print(f"🎯 Track ID: {track_id}")
            print(f"📐 중앙으로부터 각도: {math.degrees(target_angle):+.2f}°")
            
            if valid_ranges:
                avg_distance = sum(valid_ranges) / len(valid_ranges)
                print(f"📍 거리: {avg_distance:.3f}m")
            else:
                print(f"📍 거리: 측정 실패")
            
            print(f"\n📡 LiDAR RAW 데이터 (거리 > 0): {len(window_data)}개")
            if window_data:
                raw_list = [f"{r:.3f}m" for _, r in sorted(window_data)]
                print(f"   {raw_list}")
            else:
                print(f"   없음")
            
            print(f"\n✅ Valid Ranges: {len(valid_ranges)}개")
            if valid_ranges:
                valid_list = [f"{r:.3f}m" for r in sorted(valid_ranges)]
                print(f"   {valid_list}")
            else:
                print(f"   없음")
            
            print(f"{'='*60}\n")
        
        if valid_ranges:
            return sum(valid_ranges) / len(valid_ranges)
        
        # 윈도우에 유효 데이터 없으면 가장 가까운 포인트 사용
        if 0.1 < ranges[best_idx] < 10.0:
            return ranges[best_idx]
        
        return None
    
    def print_distance(self):
        """거리 정보 출력"""
        try:
            if self.latest_detections is None or len(self.latest_detections) == 0:
                msg = Int32()
                msg.data = -1
                self.closest_id_pub.publish(msg)
                return
            
            # 모든 객체의 거리 계산
            detections_with_distance = []
            
            for det in self.latest_detections:
                try:
                    center_x = det.center_x
                    bbox_width = det.x_max - det.x_min
                    # track_id를 전달하여 디버그 출력
                    distance = self.get_distance_from_lidar(center_x, bbox_width, track_id=det.track_id)
                    
                    if distance is not None:
                        detections_with_distance.append({
                            'detection': det,
                            'distance': distance
                        })
                except Exception as e:
                    self.get_logger().warn(f'객체 거리 계산 에러: {e}')
                    continue
            
            if not detections_with_distance:
                # LiDAR 거리 못 구하면 비전 기반
                self.estimate_distance_from_vision()
                return
            
            # 가장 가까운 객체
            closest = min(detections_with_distance, key=lambda x: x['distance'])
            closest_detection = closest['detection']
            closest_distance = closest['distance']
            
            # ID 발행
            msg = Int32()
            msg.data = int(closest_detection.track_id)
            self.closest_id_pub.publish(msg)
            
            # CLOSEST OBJECT 정보는 로그에만 남기고 콘솔 출력 제거
            # (LiDAR 디버그 정보만 콘솔에 표시됨)
            

        except Exception as e:
            self.get_logger().error(f'print_distance 에러: {e}')
            import traceback
            traceback.print_exc()
    
    def estimate_distance_from_bbox(self, detection):
        """바운딩 박스로 거리 추정"""
        bbox_height = detection.y_max - detection.y_min
        
        if bbox_height < 10:
            return 10.0
        
        assumed_height = 1.7
        estimated_distance = (assumed_height * self.image_height) / (bbox_height * 2.0)
        
        return max(0.5, min(10.0, estimated_distance))
    
    def estimate_distance_from_vision(self):
        """비전만으로 거리 추정"""
        if not self.latest_detections:
            return
        
        detections_with_est = []
        for det in self.latest_detections:
            est_dist = self.estimate_distance_from_bbox(det)
            detections_with_est.append({
                'detection': det,
                'distance': est_dist
            })
        
        closest = min(detections_with_est, key=lambda x: x['distance'])
        closest_detection = closest['detection']
        estimated_dist = closest['distance']
        
        msg = Int32()
        msg.data = int(closest_detection.track_id)
        self.closest_id_pub.publish(msg)
        
        # 비전 기반 추정 정보는 콘솔에 출력하지 않음
    
    def cleanup(self):
        """종료 시 정리"""
        self.running = False
        if self.lidar_thread:
            self.lidar_thread.join(timeout=2.0)
        if self.laser:
            try:
                self.laser.turnOff()
                self.laser.disconnecting()
            except:
                pass


def main(args=None):
    rclpy.init(args=args)
    node = None
    
    try:
        node = DistanceLidarNode()
        
        print("\n" + "="*60)
        print("🎯 Distance LiDAR 시스템 실행 중")
        print("="*60)
        print("📍 실시간 거리 측정 중...")
        print("🛑 종료하려면 'q' + Enter를 입력하세요")
        print("="*60 + "\n")
        
        # 메인 스레드에서 입력 대기
        import select
        import sys
        
        while rclpy.ok():
            try:
                # ROS2 스핀을 짧게 실행
                rclpy.spin_once(node, timeout_sec=0.1)
                
                # 키 입력 확인 (non-blocking)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.strip().lower() == 'q':
                        print("\n🛑 사용자 종료 요청 - 시스템 종료 중...")
                        break
                        
            except KeyboardInterrupt:
                print("\n🛑 Ctrl+C 감지 - 시스템 종료 중...")
                break
            except Exception as e:
                node.get_logger().error(f'스핀 에러: {e}')
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n🛑 시스템 종료 중...")
    except Exception as e:
        print(f'\n❌ 노드 초기화 에러: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 정리 작업 중...")
        if node:
            try:
                node.cleanup()
                node.destroy_node()
            except Exception as e:
                print(f"정리 중 에러: {e}")
        try:
            rclpy.shutdown()
        except:
            pass
        print("✅ 시스템 종료 완료\n")


if __name__ == '__main__':
    main()
