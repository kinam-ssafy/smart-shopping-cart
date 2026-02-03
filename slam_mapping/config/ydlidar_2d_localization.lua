-- Cartographer Configuration for YDLidar - Pure Localization Mode
-- 저장된 맵(.pbstream)에서 현재 위치를 추정
-- 새로운 맵을 생성하지 않고 기존 맵에서 위치만 찾음

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  -- Frame 설정
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

  -- TF 타임아웃
  lookup_transform_timeout_sec = 1.0,

  -- 퍼블리시 주기 (빠른 업데이트)
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
TRAJECTORY_BUILDER_2D.num_accumulated_range_data = 2

-- 실시간 스캔 매칭 (Localization용 - 넓은 검색 범위)
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.8  -- 80cm 검색 범위 (초기 위치 찾기용)
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(90.)  -- 90도 검색 범위
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 1e-2
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e-2

-- Ceres 스캔 매칭
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 10.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 1.0
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 1.0

-- 서브맵 설정 (Localization 모드에서는 새 서브맵 생성 최소화)
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 45
TRAJECTORY_BUILDER_2D.submaps.grid_options_2d.resolution = 0.05

-- Motion Filter
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 0.5
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.1
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(5.)

-- ============================================
-- Pure Localization 설정
-- ============================================

-- Pose Graph 최적화 (Global Localization 강화)
POSE_GRAPH.optimization_problem.huber_scale = 1e1
POSE_GRAPH.optimize_every_n_nodes = 10  -- 더 자주 최적화 (빠른 위치 보정)

-- 글로벌 제약 조건 (기존 맵과의 매칭)
POSE_GRAPH.constraint_builder.min_score = 0.45  -- 매칭 임계값 낮춤 (더 많은 매칭 허용)
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.5  -- 글로벌 localization 임계값
POSE_GRAPH.constraint_builder.sampling_ratio = 0.5  -- 더 많은 제약 조건 샘플링
POSE_GRAPH.constraint_builder.loop_closure_translation_weight = 1.1e4
POSE_GRAPH.constraint_builder.loop_closure_rotation_weight = 1e5

-- 글로벌 SLAM 제약 조건 검색 (기존 서브맵에서 현재 위치 찾기)
POSE_GRAPH.constraint_builder.max_constraint_distance = 15.  -- 더 넓은 범위에서 제약 조건 검색
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.linear_search_window = 10.  -- 10m 검색 (글로벌 localization)
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.angular_search_window = math.rad(180.)  -- 전방위 검색
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.branch_and_bound_depth = 7

-- Pure Localization Trimmer (새 서브맵 제한)
-- 이 설정은 새로운 trajectory가 기존 맵에 너무 많은 서브맵을 추가하지 않도록 함
POSE_GRAPH.max_num_final_iterations = 200
POSE_GRAPH.global_sampling_ratio = 0.003  -- 글로벌 제약 조건을 자주 시도
POSE_GRAPH.global_constraint_search_after_n_seconds = 5.  -- 5초마다 글로벌 검색

return options
