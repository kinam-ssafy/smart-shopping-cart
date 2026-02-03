#!/usr/bin/env python3
"""
Cmd Vel Bridge Node
Nav2의 /cmd_vel을 STM32 모터 드라이버로 전달하는 브릿지 노드

STM32 프로토콜:
  - x=value  → 조향각 (-37 ~ 37)
  - z=value  → 전진 속도 (0 ~ 100)
  - r=value  → 후진 속도 (0 ~ 100)

기능:
- /cmd_vel (Twist) 구독
- 시뮬레이션 모드: 속도 로깅 + 가상 오도메트리 발행
- 실제 모드: STM32로 모터 명령 전송
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

import math
import time

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[WARN] pyserial not installed. Running in simulation mode only.")


class CmdVelBridge(Node):
    def __init__(self):
        super().__init__('cmd_vel_bridge')

        # 파라미터 선언
        self.declare_parameter('simulation', True)
        self.declare_parameter('serial_port', '/dev/ttyACM0')  # STM32 기본 포트
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('publish_odom', True)
        self.declare_parameter('publish_tf', False)  # Cartographer가 TF 관리하므로 기본 False

        # 속도 제한 파라미터
        self.declare_parameter('max_linear_vel', 0.22)   # m/s
        self.declare_parameter('max_angular_vel', 1.0)   # rad/s

        # STM32 제어 범위 파라미터
        self.declare_parameter('max_steer', 37)          # 최대 조향각
        self.declare_parameter('max_speed', 100)         # 최대 속도 값 (z, r)
        self.declare_parameter('min_speed', 30)          # 최소 속도 값 (너무 낮으면 안 움직임)

        # 파라미터 로드
        self.simulation = self.get_parameter('simulation').value
        self.serial_port = self.get_parameter('serial_port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.publish_odom = self.get_parameter('publish_odom').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value
        self.max_steer = self.get_parameter('max_steer').value
        self.max_speed = self.get_parameter('max_speed').value
        self.min_speed = self.get_parameter('min_speed').value

        # /cmd_vel 구독
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # 시리얼 연결
        self.serial_conn = None
        self.last_cmd = {'x': None, 'z': None, 'r': None}

        if not self.simulation:
            if not SERIAL_AVAILABLE:
                self.get_logger().warn('pyserial not available. Falling back to simulation mode.')
                self.simulation = True
            else:
                self.init_serial()

        # 시뮬레이션 모드 설정
        if self.simulation:
            self.get_logger().info('Running in SIMULATION mode')
            self.get_logger().info('cmd_vel commands will be logged but not sent to motors.')

            # 시뮬레이션용 오도메트리 발행
            if self.publish_odom:
                self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

            # TF 브로드캐스터 (선택적)
            if self.publish_tf:
                self.tf_broadcaster = TransformBroadcaster(self)

            # 시뮬레이션 상태
            self.x = 0.0
            self.y = 0.0
            self.theta = 0.0
            self.last_time = self.get_clock().now()

            # 현재 속도
            self.current_linear_x = 0.0
            self.current_angular_z = 0.0

            # 오도메트리 발행 타이머 (20Hz)
            if self.publish_odom:
                self.odom_timer = self.create_timer(0.05, self.publish_odom_callback)
        else:
            self.get_logger().info(f'Running in REAL mode - STM32 on {self.serial_port}')

        # 통계
        self.cmd_count = 0
        self.last_cmd_time = None

        # 안전 타이머 (0.5초 동안 cmd_vel이 없으면 정지)
        self.safety_timer = self.create_timer(0.1, self.safety_check)
        self.last_cmd_received_time = time.time()
        self.SAFETY_TIMEOUT = 0.5  # 초

        self.get_logger().info('Cmd Vel Bridge started')
        self.get_logger().info(f'  Max linear: {self.max_linear_vel} m/s')
        self.get_logger().info(f'  Max angular: {self.max_angular_vel} rad/s')
        self.get_logger().info(f'  Max steer: {self.max_steer}')
        self.get_logger().info(f'  Speed range: {self.min_speed} ~ {self.max_speed}')

    def init_serial(self):
        """STM32 시리얼 포트 초기화"""
        try:
            self.serial_conn = serial.Serial(
                self.serial_port,
                self.baudrate,
                timeout=0.1
            )
            time.sleep(2)  # STM32 리셋 대기
            self.get_logger().info(f'STM32 connected on {self.serial_port}')
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.get_logger().warn('Falling back to simulation mode')
            self.simulation = True
            self.serial_conn = None

    def cmd_vel_to_stm32(self, linear_x: float, angular_z: float):
        """
        cmd_vel (Twist)를 STM32 명령으로 변환

        Args:
            linear_x: 전진 속도 (m/s), 양수=전진, 음수=후진
            angular_z: 회전 속도 (rad/s), 양수=좌회전, 음수=우회전

        Returns:
            (x_steer, z_forward, r_backward) 튜플
        """
        # 1. 조향각 계산 (angular_z -> x)
        # angular_z가 양수면 좌회전 -> x가 음수
        # angular_z가 음수면 우회전 -> x가 양수
        # 범위: -max_angular_vel ~ max_angular_vel -> -max_steer ~ max_steer
        if abs(angular_z) > 0.01:
            x_steer = -angular_z / self.max_angular_vel * self.max_steer
            x_steer = max(-self.max_steer, min(self.max_steer, x_steer))
        else:
            x_steer = 0

        # 2. 속도 계산 (linear_x -> z 또는 r)
        # linear_x가 양수면 전진 (z)
        # linear_x가 음수면 후진 (r)
        z_forward = 0
        r_backward = 0

        if abs(linear_x) > 0.01:
            # 속도 스케일링: 0 ~ max_linear_vel -> min_speed ~ max_speed
            speed_ratio = abs(linear_x) / self.max_linear_vel
            speed_value = int(self.min_speed + speed_ratio * (self.max_speed - self.min_speed))
            speed_value = max(0, min(self.max_speed, speed_value))

            if linear_x > 0:
                z_forward = speed_value
            else:
                r_backward = speed_value

        return int(x_steer), z_forward, r_backward

    def send_to_stm32(self, x_steer: int, z_forward: int, r_backward: int):
        """STM32로 명령 전송 (변경된 값만)"""
        if self.serial_conn is None:
            return

        try:
            commands = []

            # 조향각 (변경 시에만 전송)
            if self.last_cmd['x'] != x_steer:
                commands.append(f"x={x_steer}")
                self.last_cmd['x'] = x_steer

            # 전진 속도
            if self.last_cmd['z'] != z_forward:
                commands.append(f"z={z_forward}")
                self.last_cmd['z'] = z_forward

            # 후진 속도
            if self.last_cmd['r'] != r_backward:
                commands.append(f"r={r_backward}")
                self.last_cmd['r'] = r_backward

            # 명령 전송
            if commands:
                cmd_str = '\n'.join(commands) + '\n'
                self.serial_conn.write(cmd_str.encode())

                if self.cmd_count % 10 == 0:
                    self.get_logger().info(
                        f'[STM32] x={x_steer}, z={z_forward}, r={r_backward}'
                    )

        except Exception as e:
            self.get_logger().error(f'Serial write error: {e}')

    def cmd_vel_callback(self, msg: Twist):
        """cmd_vel 콜백"""
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        # 속도 제한
        linear_x = max(-self.max_linear_vel, min(self.max_linear_vel, linear_x))
        angular_z = max(-self.max_angular_vel, min(self.max_angular_vel, angular_z))

        self.cmd_count += 1
        self.last_cmd_received_time = time.time()

        if self.simulation:
            # 시뮬레이션 모드: 현재 속도 저장
            self.current_linear_x = linear_x
            self.current_angular_z = angular_z

            # STM32 명령으로 변환하여 로그 출력
            x_steer, z_forward, r_backward = self.cmd_vel_to_stm32(linear_x, angular_z)

            # 로그 출력 (1초에 한 번)
            if self.cmd_count % 10 == 0:
                self.get_logger().info(
                    f'[SIM] linear.x={linear_x:.3f} m/s, angular.z={angular_z:.3f} rad/s'
                )
                self.get_logger().info(
                    f'      -> STM32: x={x_steer}, z={z_forward}, r={r_backward}'
                )
        else:
            # 실제 모드: STM32로 전송
            x_steer, z_forward, r_backward = self.cmd_vel_to_stm32(linear_x, angular_z)
            self.send_to_stm32(x_steer, z_forward, r_backward)

    def safety_check(self):
        """안전 타이머: 일정 시간 동안 cmd_vel이 없으면 정지"""
        if time.time() - self.last_cmd_received_time > self.SAFETY_TIMEOUT:
            if not self.simulation and self.serial_conn:
                # 모든 값이 0이 아닌 경우에만 정지 명령 전송
                if self.last_cmd['z'] != 0 or self.last_cmd['r'] != 0:
                    self.get_logger().warn('Safety timeout - stopping motors')
                    self.send_to_stm32(0, 0, 0)

            if self.simulation:
                self.current_linear_x = 0.0
                self.current_angular_z = 0.0

    def publish_odom_callback(self):
        """시뮬레이션 오도메트리 발행"""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        # 위치 업데이트 (간단한 2D 운동학)
        if abs(self.current_angular_z) < 0.001:
            # 직선 운동
            self.x += self.current_linear_x * math.cos(self.theta) * dt
            self.y += self.current_linear_x * math.sin(self.theta) * dt
        else:
            # 원호 운동
            radius = self.current_linear_x / self.current_angular_z
            self.x += radius * (math.sin(self.theta + self.current_angular_z * dt) - math.sin(self.theta))
            self.y += radius * (math.cos(self.theta) - math.cos(self.theta + self.current_angular_z * dt))

        self.theta += self.current_angular_z * dt

        # theta 정규화 (-pi ~ pi)
        while self.theta > math.pi:
            self.theta -= 2 * math.pi
        while self.theta < -math.pi:
            self.theta += 2 * math.pi

        # Odometry 메시지 생성
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame

        # 위치
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        # 방향 (쿼터니언)
        odom_msg.pose.pose.orientation.z = math.sin(self.theta / 2)
        odom_msg.pose.pose.orientation.w = math.cos(self.theta / 2)

        # 속도
        odom_msg.twist.twist.linear.x = self.current_linear_x
        odom_msg.twist.twist.angular.z = self.current_angular_z

        # 공분산 (대각선만 설정)
        odom_msg.pose.covariance[0] = 0.01  # x
        odom_msg.pose.covariance[7] = 0.01  # y
        odom_msg.pose.covariance[35] = 0.01  # theta
        odom_msg.twist.covariance[0] = 0.01
        odom_msg.twist.covariance[35] = 0.01

        self.odom_pub.publish(odom_msg)

        # TF 발행 (선택적)
        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = self.odom_frame
            t.child_frame_id = self.base_frame
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.z = math.sin(self.theta / 2)
            t.transform.rotation.w = math.cos(self.theta / 2)
            self.tf_broadcaster.sendTransform(t)

    def emergency_stop(self):
        """비상 정지"""
        if self.serial_conn:
            try:
                self.serial_conn.write(b"x=0\nz=0\nr=0\n")
                self.last_cmd = {'x': 0, 'z': 0, 'r': 0}
                self.get_logger().info('Emergency stop sent')
            except Exception as e:
                self.get_logger().error(f'Emergency stop failed: {e}')

    def destroy_node(self):
        """노드 종료 시 정리"""
        self.get_logger().info('Shutting down cmd_vel_bridge...')

        # 모터 정지
        if self.serial_conn:
            try:
                self.serial_conn.write(b"x=0\nz=0\nr=0\n")
                time.sleep(0.1)
                self.serial_conn.close()
                self.get_logger().info('STM32 disconnected')
            except:
                pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = CmdVelBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
