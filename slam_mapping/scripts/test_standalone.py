#!/usr/bin/env python3
"""
============================================
SLAM 테스트 (독립 실행 - ROS2 빌드 없이)
============================================
ROS2 패키지 빌드 없이 바로 테스트할 수 있습니다.
YDLidar 데이터를 읽어 실시간으로 맵을 생성하고 시각화합니다.

사용법:
    python3 test_standalone.py [--port /dev/ttyUSB0]

필요:
    pip3 install numpy matplotlib
"""

import sys
import os
import math
import argparse
import threading
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# YDLidar SDK - Dynamic path resolution
ydlidar_sdk_path = os.path.expanduser('~/YDLidar-SDK/build/python')
if os.path.exists(ydlidar_sdk_path):
    sys.path.insert(0, ydlidar_sdk_path)

try:
    import ydlidar
except ImportError:
    print("YDLidar SDK not found!")
    sys.exit(1)


class OccupancyGridSLAM:
    """Occupancy Grid 기반 간단한 SLAM"""

    def __init__(self, size=20.0, resolution=0.05):
        self.size = size
        self.resolution = resolution
        self.width = int(size / resolution)
        self.height = int(size / resolution)

        # Log-odds 맵
        self.log_odds = np.zeros((self.height, self.width), dtype=np.float32)

        # 로봇 포즈 (중심에서 시작)
        self.pose = np.array([size/2, size/2, 0.0])

        # 이전 스캔
        self.prev_scan = None

        # 궤적
        self.trajectory = deque(maxlen=1000)

        # 파라미터
        self.l_occ = 0.7
        self.l_free = -0.4

    def update(self, angles, ranges):
        """스캔으로 맵 업데이트"""
        valid = np.isfinite(ranges) & (ranges > 0.12) & (ranges < 10.0)
        if not np.any(valid):
            return

        angles = angles[valid]
        ranges = ranges[valid]

        # 로컬 좌표
        lx = ranges * np.cos(angles)
        ly = ranges * np.sin(angles)
        curr_scan = np.column_stack((lx, ly))

        # 스캔 매칭
        if self.prev_scan is not None and len(self.prev_scan) > 10:
            delta = self._match(self.prev_scan, curr_scan)
            self.pose += delta
            self.trajectory.append(self.pose[:2].copy())

        self.prev_scan = curr_scan

        # 월드 좌표 변환
        cos_t, sin_t = math.cos(self.pose[2]), math.sin(self.pose[2])
        wx = self.pose[0] + lx * cos_t - ly * sin_t
        wy = self.pose[1] + lx * sin_t + ly * cos_t

        # 맵 업데이트
        rx = int(self.pose[0] / self.resolution)
        ry = int(self.pose[1] / self.resolution)

        for x, y in zip(wx, wy):
            gx = int(x / self.resolution)
            gy = int(y / self.resolution)

            if 0 <= gx < self.width and 0 <= gy < self.height:
                self._ray_trace(rx, ry, gx, gy)
                self.log_odds[gy, gx] = np.clip(
                    self.log_odds[gy, gx] + self.l_occ, -2.0, 3.5
                )

    def _match(self, prev, curr):
        """간단한 스캔 매칭"""
        pc = np.mean(prev, axis=0)
        cc = np.mean(curr, axis=0)
        return np.array([(cc[0]-pc[0])*0.1, (cc[1]-pc[1])*0.1, 0.0])

    def _ray_trace(self, x0, y0, x1, y1):
        """Bresenham ray tracing"""
        dx, dy = abs(x1-x0), abs(y1-y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0

        while True:
            if x == x1 and y == y1:
                break
            if 0 <= x < self.width and 0 <= y < self.height:
                self.log_odds[y, x] = np.clip(
                    self.log_odds[y, x] + self.l_free, -2.0, 3.5
                )
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def get_map(self):
        """확률 맵 반환"""
        prob = 1.0 - 1.0 / (1.0 + np.exp(self.log_odds))
        grid = np.full_like(prob, 0.5)
        grid[prob > 0.65] = 1.0  # occupied
        grid[prob < 0.35] = 0.0  # free
        return grid

    def save_map(self, filename):
        """맵을 PGM/YAML로 저장"""
        from PIL import Image

        grid = self.get_map()

        # 이미지 변환 (0=free=254, 0.5=unknown=205, 1=occupied=0)
        img_data = np.zeros_like(grid, dtype=np.uint8)
        img_data[grid < 0.35] = 254  # free
        img_data[(grid >= 0.35) & (grid <= 0.65)] = 205  # unknown
        img_data[grid > 0.65] = 0  # occupied

        img_data = np.flipud(img_data)

        # PGM 저장
        img = Image.fromarray(img_data, mode='L')
        img.save(f"{filename}.pgm")

        # YAML 저장
        yaml_content = f"""image: {os.path.basename(filename)}.pgm
resolution: {self.resolution}
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
        with open(f"{filename}.yaml", 'w') as f:
            f.write(yaml_content)

        print(f"Map saved: {filename}.pgm, {filename}.yaml")


class SlamVisualizer:
    """실시간 SLAM 시각화"""

    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.slam = OccupancyGridSLAM()
        self.laser = None
        self.running = False
        self.scan_points = None
        self.lock = threading.Lock()

        self._setup_plot()

    def _setup_plot(self):
        plt.ion()
        self.fig, self.axes = plt.subplots(1, 2, figsize=(14, 6))
        self.fig.suptitle('YDLidar SLAM - Move LiDAR to build map!', fontsize=14)

        # 맵
        self.axes[0].set_title('Occupancy Grid Map')
        self.axes[0].set_aspect('equal')
        self.map_img = self.axes[0].imshow(
            self.slam.get_map(), cmap='gray_r', vmin=0, vmax=1,
            origin='lower', interpolation='nearest'
        )

        rx = self.slam.pose[0] / self.slam.resolution
        ry = self.slam.pose[1] / self.slam.resolution
        self.robot_marker, = self.axes[0].plot(rx, ry, 'r^', markersize=12)
        self.traj_line, = self.axes[0].plot([], [], 'b-', linewidth=1, alpha=0.7)

        # 스캔
        self.axes[1].set_title('LiDAR Scan')
        self.axes[1].set_xlim(-5, 5)
        self.axes[1].set_ylim(-5, 5)
        self.axes[1].set_aspect('equal')
        self.axes[1].grid(True, alpha=0.3)
        self.scan_plot, = self.axes[1].plot([], [], 'g.', markersize=2)
        self.axes[1].plot(0, 0, 'ro', markersize=10)

        self.info_text = self.axes[1].text(
            0.02, 0.98, '', transform=self.axes[1].transAxes,
            verticalalignment='top', fontsize=10,
            bbox=dict(facecolor='wheat', alpha=0.8)
        )

        plt.tight_layout()

    def init_lidar(self):
        try:
            ydlidar.os_init()
            self.laser = ydlidar.CYdLidar()

            ports = ydlidar.lidarPortList()
            port = self.port
            for k, v in ports.items():
                port = v
                print(f"Found LiDAR: {port}")

            self.laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
            self.laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
            self.laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
            self.laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
            self.laser.setlidaropt(ydlidar.LidarPropScanFrequency, 6.0)
            self.laser.setlidaropt(ydlidar.LidarPropSampleRate, 4)
            self.laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

            if self.laser.initialize() and self.laser.turnOn():
                print("YDLidar ready!")
                return True
            return False

        except Exception as e:
            print(f"Error: {e}")
            return False

    def update_plot(self):
        with self.lock:
            # 맵
            self.map_img.set_data(self.slam.get_map())

            rx = self.slam.pose[0] / self.slam.resolution
            ry = self.slam.pose[1] / self.slam.resolution
            self.robot_marker.set_data([rx], [ry])

            if len(self.slam.trajectory) > 1:
                traj = np.array(list(self.slam.trajectory))
                self.traj_line.set_data(
                    traj[:, 0] / self.slam.resolution,
                    traj[:, 1] / self.slam.resolution
                )

            # 스캔
            if self.scan_points is not None and len(self.scan_points) > 0:
                self.scan_plot.set_data(self.scan_points[:, 0], self.scan_points[:, 1])

            info = (f"Points: {len(self.scan_points) if self.scan_points is not None else 0}\n"
                   f"Pose: ({self.slam.pose[0]:.2f}, {self.slam.pose[1]:.2f})")
            self.info_text.set_text(info)

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def run(self):
        if not self.init_lidar():
            return

        self.running = True
        scan = ydlidar.LaserScan()

        print("\n" + "="*50)
        print("SLAM Running!")
        print("Move LiDAR around to build the map.")
        print("Press 's' to save map, Ctrl+C to quit.")
        print("="*50 + "\n")

        try:
            while self.running and ydlidar.os_isOk():
                if self.laser.doProcessSimple(scan) and scan.points.size() > 0:
                    angles = np.array([
                        scan.config.min_angle + i * scan.config.angle_increment
                        for i in range(scan.points.size())
                    ])
                    ranges = np.array([p.range for p in scan.points])

                    with self.lock:
                        self.slam.update(angles, ranges)

                        valid = np.isfinite(ranges) & (ranges > 0.12) & (ranges < 10.0)
                        if np.any(valid):
                            self.scan_points = np.column_stack((
                                ranges[valid] * np.cos(angles[valid]),
                                ranges[valid] * np.sin(angles[valid])
                            ))

                    self.update_plot()

                plt.pause(0.05)

        except KeyboardInterrupt:
            print("\nSaving map before exit...")
            # Dynamic path - save to maps directory relative to script location
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            maps_dir = os.path.join(script_dir, 'maps')
            os.makedirs(maps_dir, exist_ok=True)
            self.slam.save_map(os.path.join(maps_dir, "test_map"))

        finally:
            self.running = False
            if self.laser:
                self.laser.turnOff()
                self.laser.disconnecting()
            plt.close('all')


def main():
    parser = argparse.ArgumentParser(description='SLAM Test')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='LiDAR port')
    args = parser.parse_args()

    if os.path.exists(args.port):
        os.system(f'sudo chmod 666 {args.port}')

    viz = SlamVisualizer(port=args.port)
    viz.run()


if __name__ == '__main__':
    main()
