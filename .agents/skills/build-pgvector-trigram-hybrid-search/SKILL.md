---
name: build-pgvector-trigram-hybrid-search
description: Stage 2 workflow for generating multilingual-e5-large embeddings, indexing with HNSW and GIN trigram, and implementing single-query hybrid search engine.
---

# Stage 2: Build pgvector & Trigram Hybrid Search

## Objectives
1. **Multilingual Embeddings:**
   - Embed `products.search_text` using `intfloat/multilingual-e5-large` with passage prefix: `"passage: <search_text>"`.
   - Dimension: 1024.
   - Batch insert into `products.embedding`.
2. **PostgreSQL Indexes:**
   - Create HNSW cosine index:
     `CREATE INDEX idx_products_embedding_hnsw ON products USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);`
   - Create GIN trigram index:
     `CREATE INDEX idx_products_search_text_trgm ON products USING gin (search_text gin_trgm_ops);`
3. **Single-Query Hybrid Ranking Engine:**
   - Build `src/hybrid_product_search_engine.py` with function `search_products(query: str, customer_id: str | None = None, limit: int = 10)`.
   - Embed incoming query with `"query: <normalized_query>"`.
   - Formulate single SQL query computing:
     - Semantic similarity: `1 - (p.embedding <=> %(query_embedding)s::vector)`
     - Trigram lexical similarity: `similarity(p.search_text, %(clean_query)s) + word_similarity(%(clean_query)s, p.search_text)`
     - Exact SKU match bonus
     - Logarithmic popularity score weight
     - Customer favorites boost (e.g., +0.15 if product is in customer's favorites)
   - Ensure safety constraint `WHERE p.is_active = true`.
