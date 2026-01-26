#!/usr/bin/env python3
"""
카메라 화면 확인용 디버깅용 코드입니다.
"""

import cv2

def main():
    # 0번 카메라 열기 (만약 안 되면 1, 2 등으로 변경)
    cap = cv2.VideoCapture(0)
    
    # 해상도 설정 (ROS 노드 설정과 동일하게 640x480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("✅ 카메라 뷰어 실행 중... (종료: q)")
    print("🎯 빨간 십자선에 물체를 정확히 맞추세요.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ 카메라 읽기 실패")
            break
            
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # === 중앙 십자선 그리기 (빨간색) ===
        # 가로선
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 0, 255), 2)
        # 세로선
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 0, 255), 2)
        
        # 화면 출력
        cv2.imshow('Camera Alignment Tool', frame)
        
        # 'q' 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()