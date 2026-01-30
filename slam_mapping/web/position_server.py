#!/usr/bin/env python3
"""
Position Visualization Web Server
RC카의 실시간 위치를 웹에서 시각화하는 서버
포트: 8850

사용법: python3 position_server.py [맵파일명]
예시: python3 position_server.py seoul_room4
"""

import http.server
import socketserver
import json
import os
import sys
import argparse
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# 전역 변수: 최신 위치 데이터
latest_position = {
    "x": 0.0,
    "y": 0.0,
    "theta": 0.0,
    "theta_rad": 0.0,
    "uncertainty": {"x": 0.0, "y": 0.0},
    "timestamp": 0,
    "updated_at": None
}

position_history = []
MAX_HISTORY = 100

# 맵 정보 (동적으로 업데이트됨)
MAP_INFO = {
    "resolution": 0.05,  # 미터/픽셀
    "origin": [-10.0, -10.0, 0],
    "image": "map.pgm",
    "width": 400,
    "height": 400
}

# 지정된 맵 파일 (명령줄 인자로 설정)
SPECIFIED_MAP_NAME = None


def parse_yaml_file(yaml_path):
    """YAML 파일 파싱 (멀티라인 origin 지원)"""
    result = {
        'resolution': None,
        'origin': None,
        'image': None
    }

    try:
        with open(yaml_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('resolution:'):
                result['resolution'] = float(line.split(':')[1].strip())

            elif line.startswith('image:'):
                result['image'] = line.split(':')[1].strip()

            elif line.startswith('origin:'):
                # origin 값 확인
                origin_value = line.split(':', 1)[1].strip()

                if origin_value.startswith('['):
                    # 한 줄 형식: origin: [-7.61, -24.7, 0]
                    origin_str = origin_value.strip('[]')
                    result['origin'] = [float(x.strip()) for x in origin_str.split(',')]
                elif origin_value == '' or origin_value is None:
                    # 멀티라인 형식:
                    # origin:
                    # - -7.61
                    # - -24.7
                    # - 0
                    origin_values = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-'):
                        val_str = lines[i].strip()[1:].strip()  # '-' 제거
                        origin_values.append(float(val_str))
                        i += 1
                    result['origin'] = origin_values
                    continue  # i가 이미 증가됨

            i += 1

    except Exception as e:
        print(f"[WARNING] YAML parse error: {e}")

    return result


def load_map_info_on_startup(maps_dir, map_name):
    """서버 시작 시 맵 정보를 미리 로드"""
    global MAP_INFO

    yaml_path = None
    pgm_filename = None

    # 지정된 맵 파일 사용
    if map_name:
        specified_yaml = os.path.join(maps_dir, f"{map_name}.yaml")
        if os.path.exists(specified_yaml):
            yaml_path = specified_yaml
            pgm_filename = f"{map_name}.pgm"
            print(f"[STARTUP] Loading map info from: {specified_yaml}")

    # 지정된 맵이 없으면 가장 최근 파일 사용
    if not yaml_path and os.path.exists(maps_dir):
        pgm_files = [f for f in os.listdir(maps_dir) if f.endswith('.pgm')]
        if pgm_files:
            pgm_files.sort(key=lambda x: os.path.getmtime(os.path.join(maps_dir, x)), reverse=True)
            pgm_filename = pgm_files[0]
            yaml_file = pgm_filename.replace('.pgm', '.yaml')
            yaml_path = os.path.join(maps_dir, yaml_file)
            if os.path.exists(yaml_path):
                print(f"[STARTUP] Loading map info from latest: {yaml_path}")
            else:
                yaml_path = None

    # YAML 파싱
    if yaml_path and os.path.exists(yaml_path):
        parsed = parse_yaml_file(yaml_path)

        if parsed['resolution']:
            MAP_INFO['resolution'] = parsed['resolution']
        if parsed['origin']:
            MAP_INFO['origin'] = parsed['origin']
        if pgm_filename:
            MAP_INFO['image'] = pgm_filename

        print(f"[STARTUP] MAP_INFO loaded: resolution={MAP_INFO['resolution']}, origin={MAP_INFO['origin']}")
    else:
        print(f"[WARNING] No yaml file found, using default MAP_INFO")


def get_handler_class(maps_dir, map_name):
    """맵 디렉토리와 맵 이름을 포함하는 핸들러 클래스 생성"""

    class PositionHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.maps_dir = maps_dir
            self.map_name = map_name
            super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

        def do_POST(self):
            global latest_position, position_history

            if self.path == '/api/position':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                try:
                    data = json.loads(post_data.decode('utf-8'))
                    data['updated_at'] = datetime.now().isoformat()
                    latest_position = data

                    # 히스토리에 추가
                    position_history.append({
                        "x": data.get("x", 0),
                        "y": data.get("y", 0),
                        "theta": data.get("theta", 0)
                    })
                    if len(position_history) > MAX_HISTORY:
                        position_history = position_history[-MAX_HISTORY:]

                    print(f"[Position] x={data.get('x', 0):.2f}m, y={data.get('y', 0):.2f}m, theta={data.get('theta', 0):.1f}°")

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode())

                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON decode error: {e}")
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_GET(self):
            global latest_position, position_history, MAP_INFO

            parsed = urlparse(self.path)

            if parsed.path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
                return

            if parsed.path == '/api/position':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(latest_position).encode())

            elif parsed.path == '/api/history':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(position_history).encode())

            elif parsed.path == '/api/map_info':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(MAP_INFO).encode())

            elif parsed.path == '/' or parsed.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html_path = os.path.join(os.path.dirname(__file__), 'index.html')
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())

            elif parsed.path == '/map.pgm':
                map_path = None

                # 지정된 맵 파일 사용
                if self.map_name:
                    specified_pgm = os.path.join(self.maps_dir, f"{self.map_name}.pgm")
                    specified_yaml = os.path.join(self.maps_dir, f"{self.map_name}.yaml")

                    if os.path.exists(specified_pgm):
                        map_path = specified_pgm
                        if os.path.exists(specified_yaml):
                            self._update_map_info(specified_yaml, f"{self.map_name}.pgm")
                        print(f"[MAP] Using specified map: {self.map_name}")
                    else:
                        print(f"[WARNING] Specified map not found: {specified_pgm}")

                # 지정된 맵이 없으면 가장 최근 파일 사용
                if not map_path and os.path.exists(self.maps_dir):
                    pgm_files = [f for f in os.listdir(self.maps_dir) if f.endswith('.pgm')]
                    if pgm_files:
                        pgm_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.maps_dir, x)), reverse=True)
                        map_path = os.path.join(self.maps_dir, pgm_files[0])
                        yaml_file = pgm_files[0].replace('.pgm', '.yaml')
                        yaml_path = os.path.join(self.maps_dir, yaml_file)
                        if os.path.exists(yaml_path):
                            self._update_map_info(yaml_path, pgm_files[0])
                        print(f"[MAP] Using latest map: {pgm_files[0]}")

                if map_path and os.path.exists(map_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'image/x-portable-graymap')
                    self.end_headers()
                    with open(map_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    print(f"[ERROR] Map not found in {self.maps_dir}")
                    self.send_response(404)
                    self.end_headers()
            else:
                super().do_GET()

        def _update_map_info(self, yaml_path, pgm_filename):
            """YAML 파일에서 맵 정보 읽기"""
            global MAP_INFO
            try:
                parsed = parse_yaml_file(yaml_path)

                if parsed['resolution']:
                    MAP_INFO['resolution'] = parsed['resolution']
                if parsed['origin']:
                    MAP_INFO['origin'] = parsed['origin']

                MAP_INFO['image'] = pgm_filename
                print(f"[MAP INFO] resolution={MAP_INFO['resolution']}, origin={MAP_INFO['origin']}")
            except Exception as e:
                print(f"[WARNING] Could not parse yaml: {e}")

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def log_message(self, format, *args):
            if args and isinstance(args[0], str) and '/api/' in args[0]:
                return
            super().log_message(format, *args)

    return PositionHandler


def main():
    parser = argparse.ArgumentParser(description='Position Visualization Web Server')
    parser.add_argument('map_name', nargs='?', default=None, help='Map file name (without extension)')
    parser.add_argument('--port', type=int, default=8850, help='Server port (default: 8850)')
    args = parser.parse_args()

    PORT = args.port
    maps_dir = os.path.join(os.path.dirname(__file__), '..', 'maps')
    map_name = args.map_name

    print("=" * 50)
    print("  Position Visualization Web Server")
    print("=" * 50)
    print(f"  Server: http://localhost:{PORT}")
    print(f"  API:    http://localhost:{PORT}/api/position")
    if map_name:
        print(f"  Map:    {map_name}.pgm")
    else:
        print(f"  Map:    (auto-select latest)")
    print("")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print("")

    # 맵 파일 확인
    if map_name:
        pgm_path = os.path.join(maps_dir, f"{map_name}.pgm")
        if os.path.exists(pgm_path):
            print(f"[OK] Map file found: {pgm_path}")
        else:
            print(f"[WARNING] Map file not found: {pgm_path}")
            print(f"[INFO] Will try to use latest map from {maps_dir}")

    # 서버 시작 전에 맵 정보 미리 로드
    load_map_info_on_startup(maps_dir, map_name)

    handler_class = get_handler_class(maps_dir, map_name)

    with socketserver.TCPServer(("", PORT), handler_class) as httpd:
        print(f"[INFO] Server listening on port {PORT}...")
        print("")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
