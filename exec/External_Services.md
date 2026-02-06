# 외부 서비스 정보 (External Services)

## 1. SSAFY GMS (Global Management System) API
프로젝트 내 상품 검색 및 추천 기능을 위한 벡터 임베딩 생성(RAG)에 사용되는 외부 서비스입니다.

- **서비스명**: SSAFY GMS OpenAI Proxy
- **용도**: 텍스트 임베딩 생성 (`text-embedding-3-small` 모델 사용)
- **API Endpoint**: `https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings`
- **활용 파일**: `smart_shopping_cart_back/generate_vectors_gms.py`
- **인증 정보 (API Key)**:
  - 환경변수명: `GMS_KEY`

## 2. 기타
- 없음 (본 프로젝트는 카트 하드웨어와의 통신(MQTT) 및 자체 DB 위주로 구성되어 있으며, 소셜 인증 등은 사용하지 않음)
