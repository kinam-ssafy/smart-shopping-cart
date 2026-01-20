# Smart Shopping Cart - Frontend

Next.js 기반 스마트 쇼핑 카트 프론트엔드 애플리케이션

## 🚀 빠른 시작

### 로컬 개발 환경

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (http://localhost:3000)
npm run dev
```

### Docker로 실행

```bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

## 🐳 Docker 배포 가이드

### 사전 준비

1. **환경 변수 설정**
   ```bash
   # .env.example을 복사하여 .env 파일 생성
   cp .env.example .env
   
   # 필요한 환경 변수 수정
   # - NEXT_PUBLIC_API_URL: 백엔드 API 주소
   ```

2. **Docker 설치 확인**
   ```bash
   docker --version
   docker-compose --version
   ```

### EC2 배포 절차

1. **프로젝트 코드 업로드**
   ```bash
   # Git clone 또는 파일 전송
   git clone <repository-url>
   cd S14P11A401/smart_shopping_cart_front
   ```

2. **환경 변수 설정**
   ```bash
   # .env 파일 생성 및 수정
   nano .env
   ```

3. **Docker 컨테이너 실행**
   ```bash
   # 백그라운드에서 실행
   docker-compose up -d
   
   # 상태 확인
   docker-compose ps
   ```

4. **헬스 체크**
   ```bash
   curl http://localhost:8002
   ```

### 유용한 Docker 명령어

```bash
# 컨테이너 재시작
docker-compose restart

# 이미지 재빌드 후 실행
docker-compose up -d --build

# 로그 실시간 확인
docker-compose logs -f frontend

# 컨테이너 내부 접속
docker-compose exec frontend sh

# 컨테이너 및 이미지 삭제
docker-compose down --rmi all
```

## 📦 기술 스택

- **Framework**: Next.js 16.1.2
- **UI**: React 19.2.3, Tailwind CSS 4
- **3D Graphics**: Three.js, @react-three/fiber, @react-three/drei
- **Language**: TypeScript 5

## 🏗️ 프로젝트 구조

```
smart_shopping_cart_front/
├── app/                # Next.js App Router 페이지
├── components/         # 재사용 가능한 컴포넌트
├── public/            # 정적 파일
├── Dockerfile         # Docker 이미지 빌드 설정
├── docker-compose.yml # Docker Compose 설정
└── .env.example       # 환경 변수 템플릿
```

## 🔧 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API 주소 | `http://localhost:8000` |
| `PORT` | 애플리케이션 포트 (외부) | `8080` |

## 🐛 트러블슈팅

### Docker 빌드 실패
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# 이전 이미지 삭제 후 재빌드
docker system prune -a
docker-compose up -d --build
```

### 포트 충돌
```bash
# 8080 포트를 사용 중인 프로세스 확인 (Linux/Mac)
lsof -i :8080

# 다른 포트 사용 (docker-compose.yml 수정)
ports:
  - "8100:3000"  # 호스트:컨테이너 (8000-9000 범위 내)
```

### 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose logs frontend

# 컨테이너 상태 확인
docker-compose ps
docker inspect <container-id>
```

### EC2 보안 그룹 설정
EC2에서 외부 접속을 허용하려면 보안 그룹에서 포트 8080을 열어야 합니다:
- **Type**: Custom TCP
- **Port**: 8080
- **Source**: 0.0.0.0/0 (또는 특정 IP)

> **참고**: 이 프로젝트는 EC2 포트 제한(8000-9000)에 맞춰 8080 포트를 사용합니다.

## 📝 개발 가이드

### 새로운 패키지 추가 후
```bash
# Docker 이미지 재빌드 필요
docker-compose up -d --build
```

### 코드 변경 시
```bash
# 컨테이너를 재시작하면 자동 반영 (production mode에서는 재빌드 필요)
docker-compose restart

# 또는 재빌드
docker-compose up -d --build
```

## 📄 라이선스

이 프로젝트는 팀 프로젝트입니다.
