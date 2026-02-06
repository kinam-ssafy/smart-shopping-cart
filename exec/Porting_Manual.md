# Porting Manual (포팅 매뉴얼)

## 1. 개요 (Overview)
본 문서는 **S14P11A401 (Smart Shopping Cart)** 프로젝트의 빌드, 배포 및 환경 설정을 위한 가이드입니다.

## 2. 시스템 환경 (System Environment)

### 2.1 서버 정보 (Server Info)
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: 6.14.0-1018-aws
- **CPU Arch**: x86_64
- **RAM**: 15GB

### 2.2 사용 소프트웨어 및 버전 (Software Versions)
| 구분 | 항목 | 버전 / 이미지 | 비고 |
|------|------|---------------|------|
| **Backend** | Framework | .NET Core | Dockerfile 기준 `sdk:10.0` (확인 필요, 통상 8.0/9.0 사용) |
| **Frontend** | Framework | Next.js (Node.js 20) | `node:20-alpine` |
| **Database** | RDBMS | PostgreSQL + PostGIS | `smart-cart-db` 컨테이너 |
| **Message Broker** | MQTT | Eclipse Mosquitto | `latest` |
| **Infra** | Runtime | Docker / Docker Compose | v2.24.1 이상 권장 |

## 3. 빌드 및 배포 가이드 (Build & Deploy)

### 3.1 환경 변수 설정 (Environment Variables)
배포 전 아래 환경 변수들을 `.env` 파일 또는 시스템 환경 변수로 설정해야 합니다.

#### Backend (`smart_shopping_cart_back/.env`)
| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `MQTT_BROKER` | MQTT 브로커 호스트명 | `mqtt-broker` (도커 내부) / `localhost` |
| `MQTT_PORT` | MQTT 포트 | `1883` |
| `MQTT_TOPIC` | 카트 통신 토픽 | `cart/1` |
| `MQTT_USERNAME` | MQTT 접속 계정 | `CartLidar` |
| `MQTT_PASSWORD` | MQTT 접속 암호 | `***REDACTED-MQTT-PW***` |
| `DB_USER` | DB 사용자명 | `myuser` |
| `DB_PASSWORD` | DB 비밀번호 | `my-secure-password-123` |
| `DB_NAME` | DB 데이터베이스명 | `smart_cart` |
| `GMS_KEY` | SSAFY GMS API 키 | `S14P12A401...` |

#### Frontend (`smart_shopping_cart_front/.env` / `Dockerfile` ARG)
| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API 주소 | `https://i14a401.p.ssafy.io` |

### 3.2 배포 순서 (Deployment Steps)

1. **소스 클론**:
   ```bash
   git clone [Repository URL] S14P11A401
   cd S14P11A401
   ```

2. **Backend 배포**:
   ```bash
   cd smart_shopping_cart_back
   # .env 파일 생성 (위 환경변수 참조)
   docker-compose up -d --build
   ```

3. **Frontend 배포**:
   ```bash
   cd ../smart_shopping_cart_front
   # Docker 이미지 빌드 및 실행
   docker build --build-arg NEXT_PUBLIC_API_URL=https://... -t smart-cart-frontend .
   docker run -d -p 8002:3000 --name smart-cart-frontend smart-cart-frontend
   ```

4. **Infra (MQTT) 배포**:
   ```bash
   cd ../infra
   docker-compose up -d
   ```

### 3.3 배포 시 특이사항
- **MQTT**: `infra` 폴더의 mosquitto 컨테이너가 먼저 실행되어 있어야 백엔드가 정상적으로 MQTT 브로커에 연결됩니다.
- **DB Init**: 백엔드 최초 실행 시 `db/init` 폴더의 SQL 스크립트들이 자동으로 실행되어 테이블 및 초기 데이터(벡터 데이터 포함)가 생성됩니다.
- **Port**:
  - Backend API: `8123` (External) -> `5000` (Internal)
  - Frontend: `8002` (External) -> `3000` (Internal)
  - MQTT: `8883` (External/SSL) -> `1883` (Internal)

## 4. 데이터베이스 접속 정보 (DB Connection)
- **Host**: `localhost` (외부) 또는 `db` (도커 내부 네트워크 `cart-network`)
- **Port**: `5432`
- **Database**: `smart_cart`
- **User**: `myuser`
- **Password**: `my-secure-password-123`
