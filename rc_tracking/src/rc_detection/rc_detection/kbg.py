#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

from ultralytics import YOLO

class MinimalImageViewer(Node):
    def __init__(self):
        super().__init__('minimal_image_viewer')

        self.bridge = CvBridge()
        self.window_name = "kbg_viewer"
        self.gui_enabled = bool(os.environ.get("DISPLAY"))

        if self.gui_enabled:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        else:
            self.get_logger().warn("DISPLAY가 비어있음. MobaXterm X11 포워딩 켜야 창이 뜹니다.")

        # ✅ yolo26s.engine 경로(스크린샷 기준: rc_tracking 루트에 있음)
        ws_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.engine_path = os.path.join(ws_root, "yolo26s.engine")

        # ✅ YOLO(TensorRT engine) 로드 (1회)
        self.get_logger().info(f"Loading model: {self.engine_path}")
        self.model = YOLO(self.engine_path)

        # 곰인형(=COCO class 77)만
        self.target_cls = 77
        self.conf_thres = 0.25

        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.cb,
            qos_profile_sensor_data
        )

    def cb(self, msg):
        if not self.gui_enabled:
            return

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # ✅ 곰인형(class 77)만 추론
        results = self.model.predict(
            source=frame,
            classes=[self.target_cls],
            conf=self.conf_thres,
            verbose=False
        )

        # ✅ 박스 그리기
        if results and results[0].boxes is not None:
            for b in results[0].boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                conf = float(b.conf[0]) if b.conf is not None else 0.0

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, f"teddy {conf:.2f}", (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow(self.window_name, frame)
        cv2.waitKey(1)

def main():
    rclpy.init()
    node = MinimalImageViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        try:
            rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()

