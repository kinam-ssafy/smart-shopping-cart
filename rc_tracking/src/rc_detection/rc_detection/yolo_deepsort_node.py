#!/usr/bin/env python3
"""
YOLO Detection and DeepSORT Tracking Node
Detects objects using YOLOv11n and tracks them with DeepSORT
Publishes bounding boxes for sensor fusion
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, Int32
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# Custom messages (you'll need to build these)
try:
    from rc_detection.msg import Detection, DetectionArray
    print("✅ Detection 메시지 import 성공")
except ImportError as e:
    # Fallback for testing - use standard messages
    print(f"❌ Detection 메시지 import 실패: {e}")
    from std_msgs.msg import String
    Detection = None
    DetectionArray = None


class YOLODeepSORTNode(Node):
    def __init__(self):
        super().__init__('yolo_deepsort_node')
        
        # Parameters
        self.declare_parameter('model_path', 'yolo26n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('target_class', 'person')  # 추적할 대상 클래스
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('show_preview', True)
        
        model_path = self.get_parameter('model_path').value
        self.conf_threshold = self.get_parameter('confidence_threshold').value
        self.target_class = self.get_parameter('target_class').value
        image_topic = self.get_parameter('image_topic').value
        self.show_preview = self.get_parameter('show_preview').value
        
        # Initialize YOLO
        self.get_logger().info(f'Loading YOLO model: {model_path}')
        self.yolo = YOLO(model_path)
        
        # Initialize DeepSORT
        self.tracker = DeepSort(
            max_age=30,
            n_init=1,  # Reduced from 3 to 1 for faster confirmation
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=None,
            embedder="mobilenet",
            half=True,
            embedder_gpu=True
        )
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Distance tracking (from sensor fusion)
        self.latest_distance = None
        self.distance_timestamp = None
        
        # Closest object tracking
        self.closest_object_id = None
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )
        
        self.distance_sub = self.create_subscription(
            Float32,
            '/distance',
            self.distance_callback,
            10
        )
        
        self.closest_id_sub = self.create_subscription(
            Int32,
            '/closest_object_id',
            self.closest_id_callback,
            10
        )
        
        # Publishers
        if DetectionArray is not None:
            self.detection_pub = self.create_publisher(
                DetectionArray,
                '/detections',
                10
            )
        
        # For visualization
        self.latest_frame = None
        
        self.get_logger().info('YOLO + DeepSORT node initialized')
        self.get_logger().info(f'Target class: {self.target_class}')
    
    def distance_callback(self, msg):
        """Receive distance data from sensor fusion"""
        self.latest_distance = msg.data
        self.distance_timestamp = self.get_clock().now()
    
    def closest_id_callback(self, msg):
        """Receive closest object ID"""
        self.closest_object_id = msg.data if msg.data >= 0 else None
    
    def image_callback(self, msg):
        """Process incoming camera images"""
        try:
            # Convert ROS Image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.latest_frame = cv_image.copy()
            
            # Run YOLO detection
            results = self.yolo(cv_image, conf=self.conf_threshold, verbose=False)
            
            # Prepare detections for DeepSORT
            detections_for_tracker = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = self.yolo.names[cls]
                    
                    # Filter by target class if specified
                    if self.target_class and class_name != self.target_class:
                        continue
                    
                    # Format: ([x1, y1, width, height], confidence, class_name)
                    w = x2 - x1
                    h = y2 - y1
                    detections_for_tracker.append((
                        [x1, y1, w, h],
                        conf,
                        class_name
                    ))
            
            # Update tracker
            tracks = self.tracker.update_tracks(
                detections_for_tracker,
                frame=cv_image
            )
            
            # Publish detections
            self.publish_detections(tracks, msg.header)
            
            # Visualize if enabled
            if self.show_preview:
                self.visualize(cv_image, tracks)
                
        except Exception as e:
            self.get_logger().error(f'Error in image_callback: {str(e)}')
    
    def publish_detections(self, tracks, header):
        """Publish tracked detections"""
        if DetectionArray is None:
            self.get_logger().error('❌ DetectionArray is None - cannot publish')
            return
        
        self.get_logger().debug(f'Publishing {len(tracks)} tracks')
        detection_array = DetectionArray()
        detection_array.header = header
        
        confirmed_count = 0
        for track in tracks:
            if not track.is_confirmed():
                continue
            confirmed_count += 1
            
            track_id = track.track_id
            ltrb = track.to_ltrb()
            
            detection = Detection()
            detection.track_id = int(track_id)
            detection.class_name = track.get_det_class() if hasattr(track, 'get_det_class') else 'unknown'
            
            # Safely get confidence
            conf = track.get_det_conf() if hasattr(track, 'get_det_conf') else None
            detection.confidence = float(conf) if conf is not None else 0.0
            
            detection.x_min = int(ltrb[0])
            detection.y_min = int(ltrb[1])
            detection.x_max = int(ltrb[2])
            detection.y_max = int(ltrb[3])
            
            detection.center_x = float((ltrb[0] + ltrb[2]) / 2.0)
            detection.center_y = float((ltrb[1] + ltrb[3]) / 2.0)
            
            detection_array.detections.append(detection)
        
        self.detection_pub.publish(detection_array)
        
        self.get_logger().info(
            f'Total tracks: {len(tracks)}, Confirmed: {confirmed_count}, Published: {len(detection_array.detections)}',
            throttle_duration_sec=1.0
        )
    
    def visualize(self, image, tracks):
        """Visualize detections and tracks with distance information"""
        vis_image = image.copy()
        
        # Check if distance data is recent (within 0.5 seconds)
        distance_valid = False
        if self.latest_distance is not None and self.distance_timestamp is not None:
            time_diff = (self.get_clock().now() - self.distance_timestamp).nanoseconds / 1e9
            distance_valid = time_diff < 0.5
        
        for track in tracks:
            if not track.is_confirmed():
                continue
            
            track_id = track.track_id
            ltrb = track.to_ltrb()
            
            # 가장 가까운 객체는 빨간색, 나머지는 초록색
            is_closest = (self.closest_object_id is not None and 
                         track_id == self.closest_object_id)
            
            box_color = (0, 0, 255) if is_closest else (0, 255, 0)  # BGR: Red or Green
            text_color = (0, 0, 255) if is_closest else (0, 255, 0)
            
            # Draw bounding box
            x1, y1, x2, y2 = map(int, ltrb)
            thickness = 3 if is_closest else 2
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), box_color, thickness)
            
            # Draw center point
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            center_color = (0, 0, 255) if is_closest else (0, 0, 255)  # Red dot
            cv2.circle(vis_image, (center_x, center_y), 5, center_color, -1)
            
            # Draw track ID and distance
            label = f'ID: {track_id}'
            if is_closest:
                label = f'[CLOSEST] ID: {track_id}'
                if distance_valid and self.latest_distance is not None:
                    try:
                        distance_val = float(self.latest_distance)
                        label += f' | {distance_val:.2f}m'
                        # Draw distance in larger text below the box
                        distance_text = f'{distance_val:.2f}m'
                        cv2.putText(vis_image, distance_text, (x1, y2 + 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                    except (ValueError, TypeError):
                        pass  # Skip if distance value is invalid
            
            cv2.putText(vis_image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Display distance info at top of screen for closest object
        if distance_valid and self.closest_object_id is not None and self.latest_distance is not None:
            try:
                distance_val = float(self.latest_distance)
                info_text = f'Closest Object: ID {self.closest_object_id} - {distance_val:.2f}m'
                cv2.putText(vis_image, info_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            except (ValueError, TypeError):
                pass  # Skip if distance value is invalid
        
        cv2.imshow('YOLO + DeepSORT Tracking', vis_image)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = YOLODeepSORTNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
