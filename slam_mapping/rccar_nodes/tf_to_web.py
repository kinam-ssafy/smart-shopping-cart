#!/usr/bin/env python3
"""
TF to Web Publisher Node
TF 트리에서 map->base_link 변환을 읽어 웹으로 송신
Cartographer SLAM 모드에서도 작동
포트: 8850
"""

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener
import math
import json
import urllib.request
import urllib.error
from typing import Optional


class TFToWeb(Node):
    def __init__(self):
        super().__init__('tf_to_web')

        # 파라미터 선언 (포트 8850 사용)
        self.declare_parameter('web_url', 'http://localhost:8850/api/position')
        self.declare_parameter('publish_rate', 5.0)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('enable_logging', True)

        self.web_url = self.get_parameter('web_url').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.map_frame = self.get_parameter('map_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.enable_logging = self.get_parameter('enable_logging').value

        # TF 버퍼 및 리스너
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 통계
        self.tf_received_count = 0
        self.web_send_count = 0
        self.web_error_count = 0

        # 주기적 실행 타이머
        self.timer = self.create_timer(1.0 / self.publish_rate, self.read_and_send)

        # 디버그 타이머
        self.debug_timer = self.create_timer(10.0, self.print_debug_info)

        self.get_logger().info('=' * 60)
        self.get_logger().info('TF to Web node started')
        self.get_logger().info(f'  Web URL: {self.web_url}')
        self.get_logger().info(f'  Publish rate: {self.publish_rate} Hz')
        self.get_logger().info(f'  Reading TF: {self.map_frame} -> {self.base_frame}')
        self.get_logger().info('  Waiting for TF transform...')
        self.get_logger().info('=' * 60)

    def read_and_send(self):
        """TF에서 위치 읽어 웹으로 송신"""
        try:
            # TF 변환 가져오기
            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.base_frame,
                rclpy.time.Time()
            )

            self.tf_received_count += 1

            # 위치 추출
            x = transform.transform.translation.x
            y = transform.transform.translation.y

            # 쿼터니언 → 오일러 각도 변환
            q = transform.transform.rotation
            siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
            theta = math.atan2(siny_cosp, cosy_cosp)
            theta_deg = math.degrees(theta)

            # 첫 변환 수신 시 로그
            if self.tf_received_count == 1:
                self.get_logger().info('*** FIRST TF RECEIVED! ***')
                self.get_logger().info(f'    Position: x={x:.2f}m, y={y:.2f}m, theta={theta_deg:.1f} deg')

            # 웹으로 송신
            pose_data = {
                'x': round(x, 3),
                'y': round(y, 3),
                'theta': round(theta_deg, 1),
                'theta_rad': round(theta, 4),
                'uncertainty': {'x': 0.0, 'y': 0.0},  # TF는 불확실성 정보 없음
                'timestamp': transform.header.stamp.sec + transform.header.stamp.nanosec * 1e-9
            }

            self.send_to_web(pose_data)

        except Exception as e:
            # TF를 아직 못 받은 경우 (정상, 대기 중)
            if self.tf_received_count == 0:
                pass  # 조용히 대기
            else:
                self.get_logger().warn(f'TF lookup failed: {e}')

    def send_to_web(self, pose_data):
        """웹 서버로 위치 송신"""
        try:
            data = json.dumps(pose_data).encode('utf-8')

            req = urllib.request.Request(
                self.web_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=0.5) as response:
                self.web_send_count += 1
                if self.enable_logging and self.web_send_count % 10 == 0:  # 10번에 1번만 로깅
                    self.get_logger().info(
                        f'[{self.web_send_count}] Position sent: '
                        f'x={pose_data["x"]:.2f}m, '
                        f'y={pose_data["y"]:.2f}m, '
                        f'theta={pose_data["theta"]:.1f} deg'
                    )

        except urllib.error.URLError as e:
            self.web_error_count += 1
            if self.web_error_count % 10 == 0:  # 10번에 1번만 로깅
                self.get_logger().warn(f'[ERROR {self.web_error_count}] Failed to send: {e.reason}')
        except Exception as e:
            self.web_error_count += 1
            if self.web_error_count % 10 == 0:
                self.get_logger().warn(f'[ERROR {self.web_error_count}] Error: {e}')

    def print_debug_info(self):
        """디버그 정보 출력"""
        self.get_logger().info('--- Debug Status ---')
        self.get_logger().info(f'  TF transforms read: {self.tf_received_count}')
        self.get_logger().info(f'  Successfully sent to web: {self.web_send_count}')
        self.get_logger().info(f'  Web send errors: {self.web_error_count}')


def main(args=None):
    rclpy.init(args=args)
    node = TFToWeb()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
