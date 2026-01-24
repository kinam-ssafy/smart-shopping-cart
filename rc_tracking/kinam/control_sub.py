import zmq
import serial
import time
import sys
import threading
import math

# YDLidar SDK 임포트 (설치 필요)
try:
    import ydlidar
except ImportError:
    print("🚨 [에러] ydlidar 라이브러리가 없습니다. 설치 후 실행하세요.")
    sys.exit(1)

# ==========================================
# ⚙️ 1. 하드웨어 설정
# ==========================================
SERIAL_PORT = "/dev/ttyACM0"  # STM32
LIDAR_PORT = "/dev/ttyUSB0"   # 라이다 (보통 USB0)
BAUD_RATE = 115200            # STM32 속도
ZMQ_PORT = 5555               # 비전 통신 포트

# ==========================================
# ⚙️ 2. 주행 튜닝 파라미터
# ==========================================
# [조향]
KP_STEER = 0.15      # 비전 중심값 기반 조향 민감도
MAX_STEER = 30       # 조향각 제한

# [속도]
TARGET_DIST = 0.5    # 목표 거리 (0.5m 유지)
KP_SPEED = 60.0      # 속도 P게인
MAX_SPEED = 60       # 최고 속도 (안전을 위해 조금 낮춤)
MIN_SPEED = 20       # 최저 구동 속도

# [안전]
STOP_DEADZONE = 0.1  # 목표 거리 ±10cm 내외 정지
WATCHDOG_TIME = 1.0  # 비전 끊김 허용 시간
LIDAR_STOP_DIST = 0.35 # 🚨 35cm 이내 장애물 감지 시 강제 정지
LIDAR_FOV_DEG = 20   # 라이다 전방 인식 각도 (±20도)

# ==========================================
# 🔌 시리얼 연결
# ==========================================
def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        print(f"✅ STM32 연결 성공! ({SERIAL_PORT})")
        return ser
    except Exception as e:
        print(f"🚨 STM32 연결 실패: {e}")
        return None

# ==========================================
# 🔭 라이다 스레드 (사용자 코드 통합)
# ==========================================
class LidarReader(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.latest_front_min = None   # 전방 최소거리(m)
        self.latest_stamp = None
        self._stop = False
        self.laser = None

    def stop(self):
        self._stop = True

    def get_latest(self):
        with self.lock:
            return self.latest_front_min

    def _init_lidar(self):
        ydlidar.os_init()
        laser = ydlidar.CYdLidar()
        
        # 라이다 설정
        laser.setlidaropt(ydlidar.LidarPropSerialPort, LIDAR_PORT)
        laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000) # G4 등 일반적인 모델
        laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        laser.setlidaropt(ydlidar.LidarPropScanFrequency, 8.0)
        laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
        laser.setlidaropt(ydlidar.LidarPropSingleChannel, True)

        if not laser.initialize():
            raise RuntimeError("라이다 초기화 실패")
        if not laser.turnOn():
            raise RuntimeError("라이다 켜기 실패")

        self.laser = laser
        print(f"✅ 라이다 연결 성공! ({LIDAR_PORT})")
        return laser

    def run(self):
        try:
            laser = self._init_lidar()
            scan = ydlidar.LaserScan()

            while (not self._stop) and ydlidar.os_isOk():
                ok = laser.doProcessSimple(scan)
                if not ok: continue

                # 전방 데이터 필터링
                front_ranges = []
                for p in scan.points:
                    r = p.range
                    if r <= 0: continue
                    
                    # 각도 변환 (Radian -> Degree)
                    ang_deg = p.angle * 180.0 / math.pi
                    
                    # 전방 ±FOV 도 이내의 거리만 수집
                    if -LIDAR_FOV_DEG <= ang_deg <= LIDAR_FOV_DEG:
                        if 0.1 < r < 10.0: # 10cm ~ 10m 사이 유효값
                            front_ranges.append(r)

                # 최소 거리 계산
                front_min = min(front_ranges) if front_ranges else None

                with self.lock:
                    self.latest_front_min = front_min
                    self.latest_stamp = scan.stamp

        except Exception as e:
            print(f"🚨 라이다 스레드 에러: {e}")
        finally:
            if self.laser:
                self.laser.turnOff()
                self.laser.disconnecting()
            print("✅ 라이다 스레드 종료")

# ==========================================
# 🚗 메인 제어 루프
# ==========================================
def main():
    # 1. ZMQ 초기화
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{ZMQ_PORT}")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    print("📡 비전 데이터 수신 대기 중...")

    # 2. 하드웨어 초기화
    ser = init_serial()
    
    # 3. 라이다 시작 (백그라운드)
    lidar_thread = LidarReader()
    lidar_thread.start()
    time.sleep(1) # 라이다 안정화 대기

    last_recv_time = time.time()

    try:
        while True:
            # --- [A] 센서 데이터 수집 ---
            
            # 1. 라이다 데이터 (거리)
            lidar_dist = lidar_thread.get_latest()
            
            # 2. 비전 데이터 (조향)
            try:
                data = socket.recv_json(flags=zmq.NOBLOCK)
                last_recv_time = time.time()
                
                status = data.get("status", "SEARCHING")
                cx = data.get("cx", 320)
                # vision_dist = data.get("dist", 0.0) # 비전 거리는 이제 참고용
            except zmq.Again:
                # 비전 데이터 없음
                status = "NO_DATA"
                cx = 320
            
            # --- [B] 안전장치 (Emergency Stop) ---
            # 비전 인식 여부와 상관없이 라이다가 가까우면 무조건 멈춤
            if lidar_dist is not None and lidar_dist < LIDAR_STOP_DIST:
                print(f"🚨 [충돌 방지] 장애물 감지! ({lidar_dist:.2f}m)")
                if ser: ser.write(b"x=0\nz=0\nr=0\n")
                time.sleep(0.05)
                continue # 이번 루프 스킵

            # --- [C] 주행 로직 ---
            if status == "LOCKED":
                # 1. 조향 (Vision 사용)
                error_x = cx - 320
                steer_val = error_x * KP_STEER
                steer_val = max(-MAX_STEER, min(MAX_STEER, steer_val))

                # 2. 속도 (LiDAR 우선 사용)
                # 라이다 데이터가 유효하면 라이다를 쓰고, 없으면 비전/정지
                current_dist = lidar_dist if lidar_dist is not None else 0.0
                
                # 라이다가 아무것도 못 봤다면(너무 멀거나 허공) -> 정지하거나 천천히 탐색
                if current_dist == 0.0:
                    error_dist = 0
                else:
                    error_dist = current_dist - TARGET_DIST

                speed_z = 0
                speed_r = 0

                # PID 제어 및 데드존
                if abs(error_dist) < STOP_DEADZONE:
                    speed_z = 0
                    speed_r = 0
                elif error_dist > 0: # 목표보다 멀다 -> 전진
                    raw_speed = error_dist * KP_SPEED
                    final_speed = min(MAX_SPEED, max(MIN_SPEED, raw_speed))
                    speed_z = int(final_speed)
                else: # 목표보다 가깝다 -> 후진
                    raw_speed = abs(error_dist) * (KP_SPEED * 0.5)
                    final_speed = min(MAX_SPEED, max(MIN_SPEED, raw_speed))
                    speed_r = int(final_speed)

                # 명령 전송 (상쇄 간섭 방지 로직 적용)
                if ser:
                    cmd = ""
                    if speed_z > 0:
                        cmd = f"x={int(steer_val)}\nz={speed_z}\n"
                        print(f"🚀 GO   | Lidar:{current_dist:.2f}m | Spd:{speed_z}")
                    elif speed_r > 0:
                        cmd = f"x={int(steer_val)}\nr={speed_r}\n"
                        print(f"🔙 BACK | Lidar:{current_dist:.2f}m | Spd:{speed_r}")
                    else:
                        cmd = f"x={int(steer_val)}\nz=0\n"
                        print(f"🛑 STOP | Lidar:{current_dist:.2f}m")
                    
                    ser.write(cmd.encode())

            else:
                # 타겟 없음 -> 정지
                if ser: ser.write(b"x=0\nz=0\nr=0\n")
                if time.time() % 1.0 < 0.1: # 로그 도배 방지
                    print(f"Status: {status} (Waiting...)")

            # --- [D] 통신 Watchdog ---
            if time.time() - last_recv_time > WATCHDOG_TIME:
                print("🚨 [비상 정지] 비전 통신 두절!")
                if ser: ser.write(b"z=0\nr=0\n")
                last_recv_time = time.time()
            
            time.sleep(0.01) # CPU 과부하 방지

    except KeyboardInterrupt:
        print("\n🛑 종료 요청")
    finally:
        lidar_thread.stop()
        if ser:
            ser.write(b"x=0\nz=0\nr=0\n")
            ser.close()
        print("✅ 시스템 종료")

if __name__ == "__main__":
    main()