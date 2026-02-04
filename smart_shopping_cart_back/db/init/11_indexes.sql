-- RAG 청크 검색 성능 향상을 위한 HNSW 인덱스
-- pgvector 확장이 필요하며, 07_vectors.sql에서 이미 활성화됨

CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding_hnsw 
ON rag_chunks 
USING hnsw (embedding vector_cosine_ops);
