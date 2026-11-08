-- Enable pgvector and pg_trgm extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add search_text, popularity_score, and vector embedding column (768 dimensions for intfloat/multilingual-e5-base)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS search_text text,
ADD COLUMN IF NOT EXISTS popularity_score numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS embedding vector(768);
