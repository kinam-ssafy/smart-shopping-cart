-- =========================================================
-- PostGIS / Routing MVP Patch (non-destructive where possible)
-- Purpose:
--  - Enforce parent_categories ↔ fixtures 1:1 cleanly
--  - Add geometry + indexes needed for routing
--  - Add pgRouting-ready nav_nodes / nav_edges tables
--  - Add buffered fixtures view (cart clearance)
--
-- Notes:
-- 1) This script tries to be safe, but a few operations may fail if your
--    existing data violates new constraints. Run in a dev DB first.
-- 2) SRID is enforced as 0 (local/unknown). Change SRID_* constants if needed.
-- =========================================================

BEGIN;

-- -----------------------------
-- 0) Pre-req extensions (optional)
-- -----------------------------
-- For gen_random_uuid() if you use it elsewhere; harmless if already enabled.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- PostGIS (required)
CREATE EXTENSION IF NOT EXISTS postgis;

-- pgRouting (optional for later; safe to keep commented if not installed yet)
-- CREATE EXTENSION IF NOT EXISTS pgrouting;

-- -----------------------------
-- 1) SRID constants (edit here)
-- -----------------------------
-- If you later standardize to a real SRID, change these and re-run constraint edits.
-- (We keep SRID=0 for local Euclidean coordinates.)
-- SRID_LOCAL = 0

-- -----------------------------
-- 2) Fix fixtures 1:1 design
--    Make parent_category_id the PK
-- -----------------------------
-- If you already have a fixtures table, we will:
--  - rename it to fixtures_old (if needed)
--  - create a new fixtures table with enforced 1:1
--  - attempt to copy data over
-- Adjust as needed if you have production data.

DO $$
BEGIN
  IF to_regclass('public.fixtures') IS NOT NULL THEN
    -- Only rename if the new shape is not already in place
    -- (We detect by checking whether parent_category_id is already PK)
    IF NOT EXISTS (
      SELECT 1
      FROM pg_constraint c
      JOIN pg_class t ON t.oid = c.conrelid
      WHERE t.relname = 'fixtures'
        AND c.contype = 'p'
        AND pg_get_constraintdef(c.oid) ILIKE '%(parent_category_id)%'
    ) THEN
      ALTER TABLE public.fixtures RENAME TO fixtures_old;
    END IF;
  END IF;
END $$;

-- Create the new fixtures table if it doesn't exist
CREATE TABLE IF NOT EXISTS fixtures (
  parent_category_id text PRIMARY KEY
    REFERENCES parent_categories(parent_category_id) ON DELETE CASCADE,

  store_map_id text NOT NULL
    REFERENCES store_maps(store_map_id) ON DELETE CASCADE,

  fixture_geom geometry(Polygon) NOT NULL,
  label text,

  -- Optional: human-readable shelf code (A1/B3 etc). Not a PK.
  fixture_code text UNIQUE,

  -- Optional: where the cart should aim to stop to access this fixture
  access_point geometry(Point) NULL
);

-- If we renamed old fixtures, try to copy data into new fixtures
-- This assumes your old fixtures had columns:
--   parent_category_id, map_id (or store_map_id), fixture_geom, label
-- If your old schema differs, edit this insert accordingly.
DO $$
BEGIN
  IF to_regclass('public.fixtures_old') IS NOT NULL THEN
    -- Best-effort insert: supports either map_id or store_map_id column name
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='fixtures_old' AND column_name='map_id'
    ) THEN
      INSERT INTO fixtures (parent_category_id, store_map_id, fixture_geom, label)
      SELECT parent_category_id, map_id, fixture_geom, label
      FROM fixtures_old
      ON CONFLICT (parent_category_id) DO NOTHING;
    ELSIF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='fixtures_old' AND column_name='store_map_id'
    ) THEN
      INSERT INTO fixtures (parent_category_id, store_map_id, fixture_geom, label)
      SELECT parent_category_id, store_map_id, fixture_geom, label
      FROM fixtures_old
      ON CONFLICT (parent_category_id) DO NOTHING;
    END IF;
  END IF;
END $$;

-- -----------------------------
-- 3) Add routing-friendly product geometry
-- -----------------------------
ALTER TABLE products
  ADD COLUMN IF NOT EXISTS product_point geometry(Point);

-- -----------------------------
-- 4) (Optional) Move/duplicate nav point to fixtures.access_point
--    If you already store parent_categories.nav_point_geom, you can copy it.
-- -----------------------------
DO $$
BEGIN
  IF to_regclass('public.parent_categories') IS NOT NULL THEN
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='parent_categories' AND column_name='nav_point_geom'
    ) THEN
      UPDATE fixtures f
      SET access_point = pc.nav_point_geom
      FROM parent_categories pc
      WHERE f.parent_category_id = pc.parent_category_id
        AND f.access_point IS NULL
        AND pc.nav_point_geom IS NOT NULL;
    END IF;
  END IF;
END $$;

-- -----------------------------
-- 5) Add SRID sanity constraints (SRID=0)
--    NOTE: These constraints can fail if existing data uses non-zero SRID.
-- -----------------------------
-- store_maps.boundary
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'boundary_srid_chk'
  ) THEN
    ALTER TABLE store_maps
      ADD CONSTRAINT boundary_srid_chk CHECK (ST_SRID(boundary) = 0);
  END IF;
END $$;

-- fixtures.fixture_geom + access_point
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fixture_srid_chk'
  ) THEN
    ALTER TABLE fixtures
      ADD CONSTRAINT fixture_srid_chk CHECK (ST_SRID(fixture_geom) = 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fixtures_access_srid_chk'
  ) THEN
    ALTER TABLE fixtures
      ADD CONSTRAINT fixtures_access_srid_chk
      CHECK (access_point IS NULL OR ST_SRID(access_point) = 0);
  END IF;
END $$;

-- parent_categories.point_geom
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='parent_categories' AND column_name='point_geom'
  ) AND NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'pc_point_srid_chk'
  ) THEN
    ALTER TABLE parent_categories
      ADD CONSTRAINT pc_point_srid_chk
      CHECK (point_geom IS NULL OR ST_SRID(point_geom) = 0);
  END IF;
END $$;

-- products.product_point
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'product_point_srid_chk'
  ) THEN
    ALTER TABLE products
      ADD CONSTRAINT product_point_srid_chk
      CHECK (product_point IS NULL OR ST_SRID(product_point) = 0);
  END IF;
END $$;

-- -----------------------------
-- 6) Spatial indexes (GiST)
-- -----------------------------
CREATE INDEX IF NOT EXISTS store_maps_boundary_gix
  ON store_maps USING GIST (boundary);

CREATE INDEX IF NOT EXISTS fixtures_geom_gix
  ON fixtures USING GIST (fixture_geom);

CREATE INDEX IF NOT EXISTS fixtures_access_gix
  ON fixtures USING GIST (access_point);

CREATE INDEX IF NOT EXISTS products_point_gix
  ON products USING GIST (product_point);

CREATE INDEX IF NOT EXISTS parent_categories_point_gix
  ON parent_categories USING GIST (point_geom);

-- -----------------------------
-- 7) Routing network tables (pgRouting-ready)
-- -----------------------------
CREATE TABLE IF NOT EXISTS nav_nodes (
  node_id bigserial PRIMARY KEY,
  store_map_id text NOT NULL REFERENCES store_maps(store_map_id) ON DELETE CASCADE,
  geom geometry(Point) NOT NULL,
  CONSTRAINT nav_node_srid_chk CHECK (ST_SRID(geom) = 0)
);

CREATE INDEX IF NOT EXISTS nav_nodes_geom_gix
  ON nav_nodes USING GIST (geom);

CREATE TABLE IF NOT EXISTS nav_edges (
  edge_id bigserial PRIMARY KEY,
  store_map_id text NOT NULL REFERENCES store_maps(store_map_id) ON DELETE CASCADE,

  source bigint NOT NULL REFERENCES nav_nodes(node_id) ON DELETE CASCADE,
  target bigint NOT NULL REFERENCES nav_nodes(node_id) ON DELETE CASCADE,

  geom geometry(LineString) NOT NULL,
  cost double precision NOT NULL,
  reverse_cost double precision NOT NULL,

  CONSTRAINT nav_edge_srid_chk CHECK (ST_SRID(geom) = 0),
  CONSTRAINT nav_edge_positive_cost_chk CHECK (cost >= 0 AND reverse_cost >= 0)
);

CREATE INDEX IF NOT EXISTS nav_edges_geom_gix
  ON nav_edges USING GIST (geom);

CREATE INDEX IF NOT EXISTS nav_edges_src_idx
  ON nav_edges (source);

CREATE INDEX IF NOT EXISTS nav_edges_tgt_idx
  ON nav_edges (target);

-- -----------------------------
-- 8) Buffered fixtures view (cart clearance)
--    Edit buffer distance (meters) to match your cart radius + safety margin.
-- -----------------------------
DROP VIEW IF EXISTS fixtures_buffered;

CREATE VIEW fixtures_buffered AS
SELECT
  parent_category_id,
  store_map_id,
  ST_Buffer(fixture_geom, 0.35) AS geom  -- <-- edit me
FROM fixtures;

COMMIT;

-- =========================================================
-- Optional cleanup:
--   DROP TABLE fixtures_old;
-- =========================================================
