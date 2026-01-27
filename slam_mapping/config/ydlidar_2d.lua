-- Cartographer Configuration for YDLidar X4-Pro
-- 2D SLAM (노트북 테스트용 - 오도메트리 없이 동작)
-- TF 간소화 + 고해상도 매핑 버전

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  -- Frame 설정 (간소화: map -> base_link -> laser)
  -- Cartographer가 odom을 자동 생성하도록 설정
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",

  -- Cartographer가 map -> odom -> base_link TF를 모두 관리
  provide_odom_frame = true,
  publish_frame_projected_to_2d = true,
  use_pose_extrapolator = true,

  -- 센서 사용 설정 (오도메트리 없음)
  use_odometry = false,
  use_nav_sat = false,
  use_landmarks = false,

  -- LiDAR 설정
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,

  -- TF 타임아웃 (더 여유있게)
  lookup_transform_timeout_sec = 1.0,

  -- 퍼블리시 주기 (더 자주 업데이트)
  submap_publish_period_sec = 0.1,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,

  -- 샘플링
  rangefinder_sampling_ratio = 1.0,
  odometry_sampling_ratio = 1.0,
  fixed_frame_pose_sampling_ratio = 1.0,
  imu_sampling_ratio = 1.0,
  landmarks_sampling_ratio = 1.0,
}

-- 2D SLAM 사용
MAP_BUILDER.use_trajectory_builder_2d = true
MAP_BUILDER.num_background_threads = 4

-- 2D Trajectory Builder 설정
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.min_range = 0.1
TRAJECTORY_BUILDER_2D.max_range = 12.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.0
TRAJECTORY_BUILDER_2D.num_accumulated_range_data = 2  -- 2개 스캔 누적으로 안정성 향상

-- 실시간 스캔 매칭 (큰 검색 윈도우로 이동 추적 강화)
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.5  -- 50cm 검색 범위
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(60.)  -- 60도 검색 범위
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 1e-2  -- 이동 허용
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e-2  -- 회전 허용

-- Ceres 스캔 매칭 (스캔 데이터 신뢰 강화)
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 10.0  -- 스캔 포인트 매칭 가중치 증가
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 1.0  -- 이동 제약 감소
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 1.0  -- 회전 제약 감소

-- 서브맵 설정 (더 많은 데이터로 안정적인 서브맵)
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 90  -- 더 많은 스캔으로 서브맵 완성
TRAJECTORY_BUILDER_2D.submaps.grid_options_2d.resolution = 0.05  -- 5cm/pixel (안정성 우선)

-- Motion Filter (이동 시 더 자주 업데이트)
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 0.5  -- 0.5초마다 강제 업데이트
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.1  -- 10cm 이동시 업데이트
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(5.)  -- 5도 회전시 업데이트

-- Pose Graph 최적화 (루프 클로저 강화)
POSE_GRAPH.optimization_problem.huber_scale = 1e1
POSE_GRAPH.optimize_every_n_nodes = 20  -- 더 자주 최적화
POSE_GRAPH.constraint_builder.min_score = 0.5  -- 매칭 임계값 낮춤
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.55
POSE_GRAPH.constraint_builder.sampling_ratio = 0.3  -- 더 많은 제약 조건 샘플링

return options
