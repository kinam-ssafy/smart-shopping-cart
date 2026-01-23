#!/usr/bin/env python3
"""
Map Saver Node
Subscribes to /map topic and saves it as PNG image
Provides real-time visualization of SLAM mapping
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np
import cv2
from datetime import datetime
import os


class MapSaver(Node):
    def __init__(self):
        super().__init__('map_saver')

        # Parameters
        self.declare_parameter('output_dir', '/tmp/slam_maps')
        self.declare_parameter('auto_save_interval', 10.0)  # seconds
        self.declare_parameter('map_topic', '/map')
        self.declare_parameter('show_preview', True)
        self.declare_parameter('color_mode', 'grayscale')  # grayscale, color, inverted

        self.output_dir = self.get_parameter('output_dir').value
        auto_save_interval = self.get_parameter('auto_save_interval').value
        map_topic = self.get_parameter('map_topic').value
        self.show_preview = self.get_parameter('show_preview').value
        self.color_mode = self.get_parameter('color_mode').value

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        self.get_logger().info(f'Map output directory: {self.output_dir}')

        # Subscribe to map
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            map_topic,
            self.map_callback,
            10
        )

        # Auto-save timer
        if auto_save_interval > 0:
            self.save_timer = self.create_timer(
                auto_save_interval,
                self.auto_save_callback
            )
            self.get_logger().info(f'Auto-save enabled: every {auto_save_interval}s')
        else:
            self.save_timer = None
            self.get_logger().info('Auto-save disabled')

        # Latest map data
        self.latest_map = None
        self.map_count = 0

        self.get_logger().info('Map Saver node initialized')
        self.get_logger().info(f'Listening to {map_topic}')
        self.get_logger().info(f'Color mode: {self.color_mode}')
        self.get_logger().info('Press Ctrl+C to save final map and exit')

    def occupancy_grid_to_image(self, occupancy_grid):
        """
        Convert OccupancyGrid message to OpenCV image

        OccupancyGrid values:
        - 0: Free space (white)
        - 100: Occupied (black)
        - -1: Unknown (gray)
        """
        width = occupancy_grid.info.width
        height = occupancy_grid.info.height
        resolution = occupancy_grid.info.resolution

        # Convert to numpy array
        data = np.array(occupancy_grid.data, dtype=np.int8)
        data = data.reshape((height, width))

        # Create image based on color mode
        if self.color_mode == 'grayscale':
            # Standard grayscale: white=free, black=occupied, gray=unknown
            image = np.zeros((height, width, 3), dtype=np.uint8)

            # Unknown: gray (128, 128, 128)
            image[data == -1] = [128, 128, 128]

            # Free space: white (255, 255, 255)
            image[data == 0] = [255, 255, 255]

            # Occupied: black (0, 0, 0)
            image[data == 100] = [0, 0, 0]

            # Partial occupancy (0-100)
            for val in range(1, 100):
                mask = (data == val)
                color_val = int(255 * (1.0 - val / 100.0))
                image[mask] = [color_val, color_val, color_val]

        elif self.color_mode == 'inverted':
            # Inverted: black=free, white=occupied, gray=unknown
            image = np.zeros((height, width, 3), dtype=np.uint8)
            image[data == -1] = [128, 128, 128]
            image[data == 0] = [0, 0, 0]
            image[data == 100] = [255, 255, 255]

            for val in range(1, 100):
                mask = (data == val)
                color_val = int(255 * (val / 100.0))
                image[mask] = [color_val, color_val, color_val]

        elif self.color_mode == 'color':
            # Color mode: blue=free, red=occupied, gray=unknown
            image = np.zeros((height, width, 3), dtype=np.uint8)

            # Unknown: gray
            image[data == -1] = [128, 128, 128]

            # Free space: blue
            image[data == 0] = [255, 200, 100]  # Light blue

            # Occupied: red
            image[data == 100] = [0, 0, 255]

            # Gradient for partial occupancy
            for val in range(1, 100):
                mask = (data == val)
                # Interpolate from blue to red
                blue = int(255 * (1.0 - val / 100.0))
                red = int(255 * (val / 100.0))
                image[mask] = [blue, 100, red]

        # Flip vertically (ROS convention: origin at bottom-left)
        image = cv2.flip(image, 0)

        return image, width, height, resolution

    def map_callback(self, msg):
        """Process incoming map messages"""
        try:
            self.latest_map = msg

            # Convert to image
            image, width, height, resolution = self.occupancy_grid_to_image(msg)

            # Add metadata overlay
            info_image = image.copy()

            # Text information
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            color = (0, 255, 0)  # Green

            text_lines = [
                f'Size: {width}x{height} ({width*resolution:.1f}m x {height*resolution:.1f}m)',
                f'Resolution: {resolution:.3f} m/pixel',
                f'Frame: {msg.header.frame_id}',
                f'Time: {datetime.now().strftime("%H:%M:%S")}',
            ]

            y_offset = 20
            for line in text_lines:
                cv2.putText(info_image, line, (10, y_offset),
                           font, font_scale, color, thickness)
                y_offset += 20

            # Show preview if enabled
            if self.show_preview:
                # Scale for display if too large
                max_display_size = 800
                if width > max_display_size or height > max_display_size:
                    scale = max_display_size / max(width, height)
                    display_image = cv2.resize(info_image,
                                               (int(width * scale), int(height * scale)))
                else:
                    display_image = info_image

                cv2.imshow('SLAM Map (Press S to save, Q to quit)', display_image)
                key = cv2.waitKey(1) & 0xFF

                if key == ord('s') or key == ord('S'):
                    self.save_map_image(image, msg)
                elif key == ord('q') or key == ord('Q'):
                    self.get_logger().info('Quit requested by user')
                    self.save_map_image(image, msg)
                    rclpy.shutdown()

            self.map_count += 1
            if self.map_count % 10 == 0:
                self.get_logger().info(
                    f'Received {self.map_count} maps | Size: {width}x{height}',
                    throttle_duration_sec=5.0
                )

        except Exception as e:
            self.get_logger().error(f'Error processing map: {str(e)}')

    def save_map_image(self, image, occupancy_grid):
        """Save map as PNG image"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'slam_map_{timestamp}.png'
            filepath = os.path.join(self.output_dir, filename)

            cv2.imwrite(filepath, image)

            # Also save metadata
            metadata_file = filepath.replace('.png', '_info.txt')
            with open(metadata_file, 'w') as f:
                f.write(f'SLAM Map Information\n')
                f.write(f'====================\n\n')
                f.write(f'Timestamp: {timestamp}\n')
                f.write(f'Width: {occupancy_grid.info.width} pixels\n')
                f.write(f'Height: {occupancy_grid.info.height} pixels\n')
                f.write(f'Resolution: {occupancy_grid.info.resolution} m/pixel\n')
                f.write(f'Real size: {occupancy_grid.info.width * occupancy_grid.info.resolution:.2f}m x '
                       f'{occupancy_grid.info.height * occupancy_grid.info.resolution:.2f}m\n')
                f.write(f'Origin: ({occupancy_grid.info.origin.position.x:.2f}, '
                       f'{occupancy_grid.info.origin.position.y:.2f})\n')
                f.write(f'Frame ID: {occupancy_grid.header.frame_id}\n')
                f.write(f'Color mode: {self.color_mode}\n')

            self.get_logger().info(f'✓ Map saved: {filepath}')
            self.get_logger().info(f'✓ Info saved: {metadata_file}')

        except Exception as e:
            self.get_logger().error(f'Failed to save map: {str(e)}')

    def auto_save_callback(self):
        """Auto-save timer callback"""
        if self.latest_map is not None:
            try:
                image, _, _, _ = self.occupancy_grid_to_image(self.latest_map)
                self.save_map_image(image, self.latest_map)
            except Exception as e:
                self.get_logger().error(f'Auto-save failed: {str(e)}')

    def destroy_node(self):
        """Cleanup and save final map"""
        if self.latest_map is not None:
            self.get_logger().info('Saving final map...')
            try:
                image, _, _, _ = self.occupancy_grid_to_image(self.latest_map)
                self.save_map_image(image, self.latest_map)
            except Exception as e:
                self.get_logger().error(f'Failed to save final map: {str(e)}')

        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    try:
        node = MapSaver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\nShutting down...')
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
