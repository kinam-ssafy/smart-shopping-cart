# db/Dockerfile
FROM postgres:18

# PostGIS, pgRouting, pgVector 확장 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-18-postgis-3 \
    postgresql-18-pgrouting \
    postgresql-18-pgvector \
    && rm -rf /var/lib/apt/lists/*

# init 폴더의 SQL 파일들을 자동 실행 폴더로 복사
# 알파벳 순서로 실행됨: 01_structure.sql → 02_data.sql
COPY ./init/ /docker-entrypoint-initdb.d/