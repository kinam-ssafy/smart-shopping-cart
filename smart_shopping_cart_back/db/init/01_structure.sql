-- 장바구니 DB 구축, SSE 방식으로 FE 송신
-- MQST subscribe로 장바구니 목록 하드웨어에서 받아오기
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE parent_categories (
    parent_category_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    point_geom geometry(Point),  -- grid 기반 위치
    nav_point_geom geometry(Point) NULL, -- 지도에 기록되지 않은 카테고리 존재 가능
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE categories (
  category_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  parent_category_id TEXT NULL REFERENCES parent_categories(parent_category_id),
  created_at timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_category_child UNIQUE (parent_category_id, name)
);

CREATE TABLE products (
  product_id text PRIMARY KEY,  -- index increment 찾아보기
  name text NOT NULL,
  category_id text NOT NULL REFERENCES categories(category_id),
  price numeric(12,2) NOT NULL CHECK (price >= 0),
  description text,
  active boolean NOT NULL DEFAULT true,
  bay text NOT NULL,  -- 가로 위치
  level integer NOT NULL CHECK (level >= 0), -- 세로 위치
  position_index integer NOT NULL CHECK (position_index >= 0), -- 방향(앞/뒤 등)
  stock integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE product_images (
  product_image_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id text NOT NULL REFERENCES products(product_id),
  image_url text NOT NULL,
  image_alt_text text,
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_product_image UNIQUE (product_id, image_url)
);

CREATE INDEX idx_product_images_product_id ON product_images (product_id);

/*
사용법 예시

SELECT *
FROM product_images
WHERE product_id = $1
ORDER BY sort_order ASC, created_at ASC;

*/


CREATE TABLE reviews (
  review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  image_url TEXT NOT NULL,
  image_alt_text TEXT,
  product_id TEXT NOT NULL REFERENCES products(product_id),
  rating INTEGER NOT NULL CHECK (rating >= 0 AND rating <= 5),
  content TEXT,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rag_chunks (
  chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), -- 청크 고유 id, 외부 레퍼런스로 사용하기 용이
  product_id TEXT NOT NULL REFERENCES products(product_id),
  source_type TEXT NOT NULL DEFAULT 'description', 
  chunk_index INTEGER NOT NULL, -- 청크된 텍스트 덩어리의 (순서) 번호
  chunk_text TEXT NOT NULL,  -- 임베딩된 텍스트, products.description에 포함되지만 같지는 않음
  embedding vector(768) NOT NULL, -- 숫자 정할 필요; OpenAI 기준 768/1536/etc
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (product_id, source_type, chunk_index)
);

CREATE TABLE store_maps (
  store_map_id TEXT PRIMARY KEY DEFAULT '1',
  version TEXT NOT NULL DEFAULT '1',  -- 맵 변경의 가능성 및 전후 발생한 에러 관리에 용이
  boundary geometry(Polygon) NOT NULL,
  units TEXT NOT NULL DEFAULT 'meters', -- PostGIS 좌표계 단위; UX에 필수 지표
  created_at timestamptz NOT NULL DEFAULT now()
);

-- 카트
CREATE TABLE carts (
  cart_id SERIAL PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'active',
  shopping_list TEXT[] DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 선반 위치
CREATE TABLE fixtures (
    fixture_id TEXT UNIQUE NOT NULL,
    parent_category_id TEXT PRIMARY KEY NOT NULL REFERENCES parent_categories(parent_category_id),
    map_id TEXT NOT NULL REFERENCES store_maps(store_map_id),
    fixture_geom geometry(Polygon),
    label TEXT
);

CREATE UNIQUE INDEX uq_fixtures_parent_category_id ON fixtures (parent_category_id);

