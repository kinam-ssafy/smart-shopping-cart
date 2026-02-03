#!/usr/bin/env python3
"""
Goal Bridge Node
웹 API와 Nav2 NavigateToPose 액션을 연결하는 브릿지 노드

기능:
- HTTP 서버로 웹 서버(position_server)로부터 목표 지점 수신
- Nav2 NavigateToPose 액션 클라이언트로 목표 전송
- 내비게이션 피드백을 웹 서버로 전송
- 목표 취소 처리
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path

import json
import math
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request


class GoalBridge(Node):
    def __init__(self):
        super().__init__('goal_bridge')

        # 파라미터 선언
        self.declare_parameter('bridge_port', 8851)
        self.declare_parameter('web_server_url', 'http://localhost:8850')
        self.declare_parameter('feedback_rate', 5.0)  # Hz

        self.bridge_port = self.get_parameter('bridge_port').value
        self.web_server_url = self.get_parameter('web_server_url').value
        self.feedback_rate = self.get_parameter('feedback_rate').value

        # 콜백 그룹
        self.callback_group = ReentrantCallbackGroup()

        # NavigateToPose 액션 클라이언트
        self._action_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose',
            callback_group=self.callback_group
        )

        # Path 토픽 구독 (경로 시각화용)
        self.path_sub = self.create_subscription(
            Path,
            '/plan',
            self.path_callback,
            10,
            callback_group=self.callback_group
        )

        # 상태 변수
        self.current_goal = None
        self.goal_handle = None
        self.nav_status = {
            'state': 'idle',  # idle, navigating, succeeded, failed, canceled
            'goal': None,
            'distance_remaining': 0.0,
            'path': [],
            'feedback_time': None
        }
        self.current_path = []
        self.status_lock = threading.Lock()

        # 피드백 전송 타이머
        self.feedback_timer = self.create_timer(
            1.0 / self.feedback_rate,
            self.send_status_to_web,
            callback_group=self.callback_group
        )

        # HTTP 서버 시작 (별도 스레드)
        self.http_server = None
        self.http_thread = threading.Thread(target=self.run_http_server, daemon=True)
        self.http_thread.start()

        self.get_logger().info(f'Goal Bridge started on port {self.bridge_port}')
        self.get_logger().info(f'Web server URL: {self.web_server_url}')

    def path_callback(self, msg: Path):
        """경로 토픽 콜백 - 경로를 저장하여 웹에 전송"""
        path_points = []
        for pose in msg.poses:
            path_points.append({
                'x': pose.pose.position.x,
                'y': pose.pose.position.y
            })
        with self.status_lock:
            self.current_path = path_points
            self.nav_status['path'] = path_points

    def run_http_server(self):
        """HTTP 서버 실행 (별도 스레드)"""
        handler = self.create_handler()
        self.http_server = HTTPServer(('', self.bridge_port), handler)
        self.get_logger().info(f'HTTP server listening on port {self.bridge_port}')
        self.http_server.serve_forever()

    def create_handler(self):
        """HTTP 요청 핸들러 클래스 생성"""
        bridge_node = self

        class GoalHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                # 로그 숨기기
                pass

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def do_POST(self):
                if self.path == '/goal':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)

                    try:
                        data = json.loads(post_data.decode('utf-8'))
                        x = float(data.get('x', 0))
                        y = float(data.get('y', 0))
                        theta = float(data.get('theta', 0))

                        bridge_node.get_logger().info(f'Received goal: x={x:.2f}, y={y:.2f}, theta={theta:.1f}')

                        # 비동기로 목표 전송
                        bridge_node.send_goal(x, y, theta)

                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'goal_sent'}).encode())

                    except Exception as e:
                        bridge_node.get_logger().error(f'Error processing goal: {e}')
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(e)}).encode())

                elif self.path == '/cancel':
                    bridge_node.cancel_goal()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'canceled'}).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

            def do_GET(self):
                if self.path == '/status':
                    with bridge_node.status_lock:
                        status = dict(bridge_node.nav_status)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        return GoalHandler

    def send_goal(self, x: float, y: float, theta: float):
        """Nav2에 목표 전송"""
        # 기존 목표가 있으면 취소
        if self.goal_handle is not None:
            self.get_logger().info('Canceling previous goal')
            self.goal_handle.cancel_goal_async()
            time.sleep(0.5)

        # 액션 서버 대기
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('NavigateToPose action server not available')
            with self.status_lock:
                self.nav_status['state'] = 'failed'
                self.nav_status['goal'] = {'x': x, 'y': y, 'theta': theta}
            return

        # 목표 생성
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        # theta를 쿼터니언으로 변환
        theta_rad = math.radians(theta)
        goal_msg.pose.pose.orientation.z = math.sin(theta_rad / 2)
        goal_msg.pose.pose.orientation.w = math.cos(theta_rad / 2)

        # 상태 업데이트
        with self.status_lock:
            self.current_goal = {'x': x, 'y': y, 'theta': theta}
            self.nav_status['state'] = 'navigating'
            self.nav_status['goal'] = self.current_goal
            self.nav_status['path'] = []

        self.get_logger().info(f'Sending goal to Nav2: ({x:.2f}, {y:.2f}, {theta:.1f}°)')

        # 비동기로 목표 전송
        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """목표 수락 응답 콜백"""
        self.goal_handle = future.result()

        if not self.goal_handle.accepted:
            self.get_logger().warn('Goal rejected by Nav2')
            with self.status_lock:
                self.nav_status['state'] = 'failed'
            return

        self.get_logger().info('Goal accepted by Nav2')

        # 결과 대기
        result_future = self.goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        """내비게이션 피드백 콜백"""
        feedback = feedback_msg.feedback
        current_pose = feedback.current_pose.pose

        # 남은 거리 계산
        if self.current_goal:
            dx = self.current_goal['x'] - current_pose.position.x
            dy = self.current_goal['y'] - current_pose.position.y
            distance = math.sqrt(dx * dx + dy * dy)

            with self.status_lock:
                self.nav_status['distance_remaining'] = distance
                self.nav_status['feedback_time'] = time.time()

    def result_callback(self, future):
        """내비게이션 결과 콜백"""
        result = future.result()
        status = result.status

        if status == 4:  # SUCCEEDED
            self.get_logger().info('Navigation succeeded!')
            with self.status_lock:
                self.nav_status['state'] = 'succeeded'
                self.nav_status['distance_remaining'] = 0.0
        elif status == 5:  # CANCELED
            self.get_logger().info('Navigation canceled')
            with self.status_lock:
                self.nav_status['state'] = 'canceled'
        else:
            self.get_logger().warn(f'Navigation failed with status: {status}')
            with self.status_lock:
                self.nav_status['state'] = 'failed'

        self.goal_handle = None

    def cancel_goal(self):
        """현재 목표 취소"""
        if self.goal_handle is not None:
            self.get_logger().info('Canceling current goal')
            cancel_future = self.goal_handle.cancel_goal_async()
            cancel_future.add_done_callback(self.cancel_callback)
        else:
            self.get_logger().info('No active goal to cancel')
            with self.status_lock:
                self.nav_status['state'] = 'idle'

    def cancel_callback(self, future):
        """취소 결과 콜백"""
        cancel_response = future.result()
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info('Goal successfully canceled')
        else:
            self.get_logger().warn('Goal cancellation failed')

    def send_status_to_web(self):
        """웹 서버로 상태 전송"""
        try:
            with self.status_lock:
                status_data = dict(self.nav_status)

            data = json.dumps(status_data).encode('utf-8')
            req = urllib.request.Request(
                f'{self.web_server_url}/api/nav_status',
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=1.0) as response:
                pass  # 응답 무시

        except Exception as e:
            # 웹 서버 연결 실패는 조용히 무시 (주기적으로 시도)
            pass

    def destroy_node(self):
        """노드 종료 시 정리"""
        if self.http_server:
            self.http_server.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = GoalBridge()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
