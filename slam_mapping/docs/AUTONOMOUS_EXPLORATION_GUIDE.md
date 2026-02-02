# RC Car 자율 탐색 맵핑 가이드

로봇 청소기처럼 RC카가 자율적으로 주변을 탐색하며 맵을 생성합니다.

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────┐
│           Autonomous Exploration Mapping System             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  YDLidar ──▶ Cartographer ──▶ /map (실시간 맵 생성)        │
│     │            SLAM                │                       │
│     │                                ▼                       │
│     └──────▶ Nav2 Costmaps ◀────────┘                       │
│              (장애물 + 탐색영역)                              │
│                     │                                        │
│                     ▼                                        │
│              m-explore-lite                                  │
│              - Frontier 감지                                 │
│              - 목표 선택                                     │
│                     │                                        │
│                     ▼                                        │
│              Nav2 Navigator                                  │
│              - 경로 계획                                     │
│              - /cmd_vel 발행                                 │
│                     │                                        │
│                     ▼                                        │
│              cmd_vel_bridge                                  │
│              (Twist → STM32)                                 │
│                     │                                        │
│                     ▼                                        │
│                  STM32                                       │
│              x=steer, z=forward                              │
└─────────────────────────────────────────────────────────────┘
```

## 주요 기능

- **자동 Frontier 감지**: 탐색된 영역과 미탐색 영역 경계 자동 감지
- **최적 경로 선택**: 가장 가까운 미탐색 영역으로 자동 이동
- **장애물 회피**: LiDAR 기반 실시간 장애물 회피
- **실시간 맵 생성**: Cartographer로 이동 중 맵 실시간 업데이트
- **자동 맵 저장**: Ctrl+C 또는 시간 종료 시 자동으로 맵 저장

## 사용 방법

### 1. 시뮬레이션 모드 (테스트용)

```bash
cd ~/S14P11A401/slam_mapping

# 5분간 자율 탐색 (모터 명령 로그만 출력)
./scripts/start_autonomous_mapping.sh /dev/ttyUSB0 300 /dev/ttyACM0 true
```

### 2. 실제 주행 모드

```bash
cd ~/S14P11A401/slam_mapping

# 10분간 자율 탐색 (실제 RC카 구동)
./scripts/start_autonomous_mapping.sh /dev/ttyUSB0 600 /dev/ttyACM0 false
```

### 3. 명령어 형식

```bash
./scripts/start_autonomous_mapping.sh [LiDAR포트] [탐색시간(초)] [STM32포트] [시뮬레이션]

매개변수:
  LiDAR포트      - YDLidar 시리얼 포트 (기본값: /dev/ttyUSB0)
  탐색시간       - 자율 탐색 시간 (초) (기본값: 300초 = 5분, 0=무제한)
  STM32포트      - STM32 시리얼 포트 (기본값: /dev/ttyACM0)
  시뮬레이션     - true/false (기본값: false)
```

### 4. 탐색 중지 및 맵 저장

- **수동 중지**: `Ctrl+C` 누르면 자동으로 맵 저장
- **자동 중지**: 설정한 시간이 지나면 자동으로 맵 저장

맵 저장 위치: `maps/auto_map_YYYYMMDD_HHMMSS.*`

## 탐색 파라미터 조정

### 탐색 범위 제한

`config/explore_params.yaml`:

```yaml
explore:
  ros__parameters:
    # 탐색 범위 제한 (배터리/시간 고려)
    use_boundary: true
    boundary_x_min: -10.0    # X 최소값 (m)
    boundary_x_max: 10.0     # X 최대값 (m)
    boundary_y_min: -10.0    # Y 최소값 (m)
    boundary_y_max: 10.0     # Y 최대값 (m)

    # Frontier 필터링
    min_frontier_size: 0.35  # 최소 frontier 크기 (m)
                             # 작을수록 더 세밀하게 탐색
```

### 주행 속도 조정

`config/nav2_explore_params.yaml`:

```yaml
controller_server:
  ros__parameters:
    FollowPath:
      max_vel_x: 0.22      # 최대 전진 속도 (m/s)
      min_vel_x: 0.0       # 최소 전진 속도
      max_vel_theta: 1.0   # 최대 회전 속도 (rad/s)
```

## 문제 해결

### 1. 로봇이 움직이지 않음

```bash
# Nav2 노드 상태 확인
ros2 lifecycle list /controller_server
ros2 lifecycle get /controller_server

# active가 아니면:
ros2 lifecycle set /controller_server configure
ros2 lifecycle set /controller_server activate
```

### 2. Frontier가 감지되지 않음

```bash
# Costmap 확인
ros2 topic echo /global_costmap/costmap --once

# Costmap이 없으면 Cartographer 확인
ros2 topic list | grep map
```

### 3. 로봇이 같은 곳만 맴돎

- `min_frontier_size` 값을 줄이기 (더 작은 영역도 탐색)
- `boundary_*` 값을 조정하여 탐색 범위 확장

### 4. 장애물에 부딪힘

`config/nav2_explore_params.yaml`:

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      inflation_radius: 0.35  # 장애물 팽창 반경 증가
      robot_radius: 0.15      # 로봇 반경 증가
```

### 5. 포트 충돌

```bash
# 기존 프로세스 종료
pkill -9 -f "ydlidar"
pkill -9 -f "cartographer"
pkill -9 -f "nav2"
pkill -9 -f "explore"
pkill -9 -f "cmd_vel_bridge"
```

## 탐색 전략

### 효율적인 탐색을 위한 팁

1. **시작 위치**: 방의 중앙에서 시작하면 더 효율적
2. **탐색 시간**: 일반 방 기준 5-10분 권장
3. **장애물**: 가구가 많은 경우 `min_frontier_size` 줄이기
4. **배터리**: 탐색 시간을 배터리 수명의 70% 이하로 설정

### 탐색 모니터링

웹 UI로 실시간 모니터링:
```bash
# 브라우저에서 접속
http://localhost:8850
```

- 현재 위치 (녹색 원)
- 이동 경로 (파란색 선)
- 목표 위치 (주황색 타겟)

## 고급 설정

### Cartographer 품질 조정

`config/ydlidar_2d.lua`:

```lua
-- 맵 해상도 (낮을수록 정밀)
TRAJECTORY_BUILDER_2D.submaps.resolution = 0.05

-- 스캔 매칭 품질
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 10
```

### Nav2 Planner 변경

차량형 로봇이므로 Smac Hybrid-A* 사용 권장:

```yaml
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_smac_planner/SmacPlannerHybrid"
      minimum_turning_radius: 0.40  # RC카 최소 회전 반경
```

## 성능 최적화

| 항목 | 낮은 성능 PC | 고성능 PC |
|------|--------------|-----------|
| costmap update_frequency | 1.0 Hz | 5.0 Hz |
| planner_frequency | 1.0 Hz | 3.0 Hz |
| costmap resolution | 0.05 m | 0.03 m |

## 참고

- Nav2 문서: https://navigation.ros.org/
- m-explore: https://github.com/robo-friends/m-explore-ros2
- Cartographer: https://google-cartographer-ros.readthedocs.io/
