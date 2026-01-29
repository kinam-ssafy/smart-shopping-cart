# RC Car Web Navigation Guide

저장된 맵을 사용하여 RC카의 실시간 위치를 웹에서 확인하는 방법입니다.

## 전체 워크플로우

```
┌────────────────────────────────────────────────────────────────────┐
│  Step 1: 맵 생성 (SLAM)                                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ create_slam_map │───▶│  Move Robot     │───▶│   save_map.sh   │ │
│  │      .sh        │    │  (RViz 확인)    │    │   (맵 저장)     │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                         │          │
│                                                         ▼          │
│                                               maps/my_room.pgm     │
│                                               maps/my_room.yaml    │
│                                               maps/my_room.pbstream│
└────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  Step 2: 웹 내비게이션 (Pure Localization)                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ start_navigation│───▶│   TF to Web     │───▶│   Web Browser   │ │
│  │      .sh        │    │   (위치 전송)   │    │  localhost:8850 │ │
│  │ (pbstream 로드) │    └─────────────────┘    └─────────────────┘ │
│  └─────────────────┘                                               │
└────────────────────────────────────────────────────────────────────┘
```

## 스크립트 요약

| 스크립트 | 기능 | 설명 |
|----------|------|------|
| `create_slam_map.sh` | SLAM 시작 | YDLidar + Cartographer로 맵 생성 |
| `save_map.sh` | 맵 저장 | .pgm + .yaml + **.pbstream** 저장 |
| `start_navigation.sh` | 내비게이션 | **.pbstream 로드** → 정확한 초기 위치 |

---

## Step 1: 맵 생성 및 저장

### 1-1. SLAM 시작

```bash
cd /home/seonil/S14P11A401/slam_mapping
./scripts/create_slam_map.sh /dev/ttyUSB0
```

### 1-2. 맵핑

- RC카를 천천히 이동시키며 맵 생성
- RViz에서 실시간으로 맵 생성 상태 확인

### 1-3. 맵 저장 (별도 터미널에서)

**SLAM이 실행 중인 상태**에서 새 터미널을 열고:

```bash
cd /home/seonil/S14P11A401/slam_mapping
./scripts/save_map.sh seoul_room4
```

저장되는 파일:
| 파일 | 설명 |
|------|------|
| `maps/seoul_room4.pgm` | 맵 이미지 |
| `maps/seoul_room4.yaml` | 맵 메타데이터 + 초기 위치 |
| `maps/seoul_room4.pbstream` | **Cartographer 상태 (Pure Localization용)** |

### 1-4. SLAM 종료

맵 저장 후 SLAM 터미널에서 `Ctrl+C`

---

## Step 2: 웹 내비게이션 실행 (Pure Localization)

저장된 맵을 로드하여 RC카의 실시간 위치를 정확하게 추정합니다.

### 2-1. 내비게이션 시작

```bash
cd /home/seonil/S14P11A401/slam_mapping

# 특정 맵 지정
./scripts/start_navigation.sh /dev/ttyUSB0 seoul_room4

# 또는 가장 최근 맵 사용
./scripts/start_navigation.sh /dev/ttyUSB0
```

### 2-2. 웹 브라우저에서 확인

```
http://localhost:8850
```

---

## Pure Localization 작동 원리

```
┌─────────────────┐
│  .pbstream 파일 │  ← SLAM 시 저장된 Cartographer 상태
└────────┬────────┘
         │ 로드
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Cartographer  │────▶│   현재 스캔과   │
│  (Localization) │     │   기존 맵 비교  │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   정확한 위치   │
                        │   추정 (TF)     │
                        └─────────────────┘
```

**장점:**
- 맵 생성 시의 초기 위치를 기억
- 빠르고 정확한 위치 인식
- 글로벌 localization 지원 (전체 맵에서 현재 위치 찾기)

---

## 시스템 구성

```
┌─────────────────┐
│   YDLidar S2    │
│   /scan topic   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Cartographer  │────▶│   TF to Web     │
│  (Pure Localization)  │   ROS2 Node     │
│   + .pbstream   │ TF  └────────┬────────┘
└─────────────────┘              │ HTTP POST
         ┌───────────────────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Web Server    │────▶│   Web Browser   │
│  (Port 8850)    │     │   (index.html)  │
└─────────────────┘     └─────────────────┘
```

---

## 웹 인터페이스 기능

### 화면 구성

- **맵 뷰**: 저장된 맵 이미지 표시
- **현재 위치**: 녹색 원으로 RC카 위치 표시
- **방향 화살표**: 빨간색 화살표로 바라보는 방향 표시
- **이동 경로**: 파란색 선으로 이동 경로 표시

### 정보 패널

| 항목 | 설명 |
|------|------|
| X Position | X 좌표 (미터) |
| Y Position | Y 좌표 (미터) |
| Heading | 방향각 (도) |
| Map Info | 맵 해상도, 크기, 원점 |
| Position Log | 최근 위치 기록 |

---

## 문제 해결

### pbstream 파일이 없는 경우

```bash
# 확인
ls -la maps/*.pbstream

# 없으면 맵을 다시 생성하고 저장
./scripts/create_slam_map.sh /dev/ttyUSB0
# (맵핑 후 별도 터미널에서)
./scripts/save_map.sh my_room
```

### 초기 위치가 정확하지 않은 경우

1. 맵 저장 시 SLAM이 실행 중이어야 함
2. 저장 위치에서 내비게이션 시작 권장
3. `.yaml` 파일의 `initial_pose` 확인:
   ```bash
   cat maps/my_room.yaml
   ```

### 위치가 업데이트되지 않는 경우

```bash
# TF 확인
ros2 topic echo /tf

# 노드 확인
ros2 node list
```

### LiDAR 포트 권한 오류

```bash
sudo chmod 666 /dev/ttyUSB0
```

---

## 디렉토리 구조

```
slam_mapping/
├── scripts/
│   ├── create_slam_map.sh         # SLAM 실행
│   ├── save_map.sh                # 맵 저장 (pgm+yaml+pbstream)
│   └── start_navigation.sh        # Pure Localization 내비게이션
├── config/
│   ├── ydlidar_2d.lua             # SLAM용 설정
│   └── ydlidar_2d_localization.lua # Localization용 설정
├── maps/                           # 저장된 맵 파일
│   ├── seoul_room4.pgm            # 맵 이미지
│   ├── seoul_room4.yaml           # 맵 메타 + 초기 위치
│   └── seoul_room4.pbstream       # Cartographer 상태
├── web/
│   ├── position_server.py         # HTTP 서버 (8850)
│   └── index.html                 # 웹 인터페이스
├── slam_mapping2/
│   └── tf_to_web.py               # TF→웹 전송 노드
└── WEB_NAVIGATION_GUIDE.md        # 이 파일
```

---

## 포트 정보

- **웹 서버**: 8850 (8700-8999 범위)
- **업데이트 주기**: 5Hz (200ms)

---

## 원격 접속

다른 PC에서 접속:

```bash
# RC카에서 방화벽 열기
sudo ufw allow 8850

# 다른 PC 브라우저에서
http://<RC카_IP>:8850
```
