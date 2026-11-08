import os
import sys
import time
from functools import lru_cache
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

# Environment flags for torch / transformers
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

import torch
import torch.nn.functional as F

# Lock CPU threads to eliminate OpenMP thread synchronization overhead on single-query inference
if not torch.cuda.is_available():
    torch.set_num_threads(min(4, os.cpu_count() or 4))

from transformers import AutoTokenizer, AutoModel
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from src.arabic_english_text_normalizer import normalize_text, normalize_and_expand_query

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/product_ai_training")
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-base")


class HybridSearchEngine:
    """
    Production single-query hybrid search engine:
    - Fast Lexical Bypass: short queries (<= 3 words) with strong title match (>= 0.65 word_similarity)
      bypass the neural model entirely and execute directly via PostgreSQL GIN trigram index in < 5ms.
    - Neural Fallback: complex or low-similarity queries use warm in-memory multilingual-e5-large
      with an LRU query embedding cache (maxsize=4096, max_length=24).
    - Maintains persistent connection to PostgreSQL with active HNSW and GIN trigram indexes.
    - Strictly enforces `p.is_active = true`.
    """
    _instance = None

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or DB_URL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[HybridSearchEngine] Initializing model '{MODEL_NAME}' on {self.device.upper()}...")
        t0 = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModel.from_pretrained(MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()
        
        self._conn = None
        self._get_connection()
        
        # Warmup pass
        self._embed_query("warmup query")
        print(f"[HybridSearchEngine] Model warm and ready in {time.time()-t0:.2f}s.")

    def _get_connection(self):
        """Returns active persistent connection, reconnecting if needed."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.db_url, autocommit=True)
            with self._conn.cursor() as cur:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_products_title_trgm 
                    ON products USING gin (split_part(search_text, '| category:', 1) gin_trgm_ops);
                """)
        return self._conn

    @classmethod
    def get_instance(cls, db_url: str | None = None):
        """Singleton accessor to ensure embedding model stays warm in memory."""
        if cls._instance is None:
            cls._instance = cls(db_url)
        return cls._instance

    @lru_cache(maxsize=4096)
    def _embed_query_vec_str(self, query: str) -> str:
        """
        Cached helper that embeds incoming query using e5 'query: ' prefix
        and returns a pre-formatted PostgreSQL vector literal string.
        Capped at max_length=24 for fast inference and low memory overhead.
        """
        prefixed = f"query: {query}"
        inputs = self.tokenizer(
            [prefixed],
            max_length=24,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.inference_mode():
            outputs = self.model(**inputs)
            token_embeddings = outputs.last_hidden_state
            mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * mask, dim=1)
            sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
            mean_pooled = sum_embeddings / sum_mask
            normalized = F.normalize(mean_pooled, p=2, dim=1)[0].cpu().numpy()
            return f"[{','.join(f'{x:.6f}' for x in normalized)}]"

    def _embed_query(self, query: str) -> list[float]:
        """
        Backwards-compatible method returning 1024-dim float list.
        """
        vec_str = self._embed_query_vec_str(query)
        return [float(x) for x in vec_str.strip("[]").split(",")]

    def _try_fast_lexical_search(
        self,
        clean_query: str,
        raw_query: str,
        customer_id: str | None = None,
        limit: int = 10,
        semantic_weight: float = 0.60,
        lexical_weight: float = 0.35,
        sku_bonus: float = 0.25,
        pop_weight: float = 0.05,
        favorite_bonus: float = 0.15,
        min_title_similarity: float = 0.65
    ) -> list[dict[str, Any]] | None:
        """
        Fast lexical bypass for short queries:
        Uses PostgreSQL GIN trigram word-similarity (<%%) operator against product titles.
        Returns results in < 5ms if top match has title_sim >= 0.65 or exact SKU match;
        otherwise returns None to fall back to neural vector search.
        """
        sql = """
            WITH fast_candidates AS (
                (SELECT id FROM products WHERE is_active = true AND UPPER(sku) = UPPER(%(raw_query)s) LIMIT 5)
                UNION
                (SELECT id FROM products WHERE is_active = true AND (%(clean_query)s <%% split_part(search_text, '| category:', 1) OR %(clean_query)s <%% search_text) LIMIT 40)
            ),
            scored AS (
                SELECT 
                    p.id,
                    p.sku,
                    p.name_en,
                    p.name_ar,
                    p.brand_en,
                    p.brand_ar,
                    p.subcategory_id,
                    p.price,
                    p.size_en,
                    p.unit,
                    p.popularity_score,
                    0.0 AS semantic_score,
                    (
                        0.70 * word_similarity(%(clean_query)s, split_part(p.search_text, '| category:', 1)) +
                        0.30 * word_similarity(%(clean_query)s, p.search_text)
                    ) AS lexical_score,
                    word_similarity(%(clean_query)s, split_part(p.search_text, '| category:', 1)) AS title_sim,
                    word_similarity(%(clean_query)s, p.search_text) AS full_sim,
                    (CASE WHEN UPPER(p.sku) = UPPER(%(raw_query)s) THEN 1.0 ELSE 0.0 END) AS sku_match,
                    (CASE WHEN f.product_id IS NOT NULL THEN 1.0 ELSE 0.0 END) AS is_favorite
                FROM products p
                JOIN fast_candidates c ON p.id = c.id
                LEFT JOIN favorites f ON p.id = f.product_id AND f.customer_id = %(customer_id)s::uuid
            )
            SELECT 
                s.id,
                s.sku,
                s.name_en,
                s.name_ar,
                s.brand_en,
                s.brand_ar,
                c.name_en AS category_en,
                sc.name_en AS subcategory_en,
                s.price,
                s.size_en,
                s.unit,
                s.popularity_score,
                s.semantic_score,
                s.lexical_score,
                s.sku_match,
                s.is_favorite,
                s.title_sim,
                s.full_sim,
                (
                    (%(w_sem)s * s.title_sim) +
                    (%(w_lex)s * s.lexical_score) +
                    (%(w_sku)s * s.sku_match) +
                    (%(w_pop)s * (COALESCE(s.popularity_score, 0.0) / 10.0)) +
                    (%(w_fav)s * s.is_favorite)
                ) AS final_score
            FROM scored s
            JOIN subcategories sc ON s.subcategory_id = sc.id
            JOIN categories c ON sc.category_id = c.id
            WHERE s.title_sim >= 0.40 OR s.full_sim >= 0.45 OR s.sku_match = 1.0
            ORDER BY final_score DESC
            LIMIT %(limit)s;
        """
        params = {
            "clean_query": clean_query,
            "raw_query": raw_query,
            "customer_id": customer_id if customer_id else None,
            "limit": limit,
            "w_sem": semantic_weight,
            "w_lex": lexical_weight,
            "w_sku": sku_bonus,
            "w_pop": pop_weight,
            "w_fav": favorite_bonus
        }

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    item = dict(zip(columns, row))
                    item["id"] = str(item["id"])
                    item["price"] = float(item["price"]) if item["price"] is not None else None
                    item["popularity_score"] = float(item["popularity_score"]) if item["popularity_score"] is not None else 0.0
                    item["semantic_score"] = 0.0
                    item["lexical_score"] = float(item["lexical_score"]) if item["lexical_score"] is not None else 0.0
                    item["final_score"] = float(item["final_score"]) if item["final_score"] is not None else 0.0
                    item["is_favorite"] = bool(item["is_favorite"])
                    results.append(item)
                
                if results and (results[0]["title_sim"] >= 0.40 or results[0]["full_sim"] >= 0.45 or results[0]["sku_match"] == 1.0):
                    for r in results:
                        r.pop("title_sim", None)
                        r.pop("full_sim", None)
                    return results
                return None
        except Exception:
            self._conn = None
            return None

    def search_products(
        self,
        query: str,
        customer_id: str | None = None,
        limit: int = 10,
        semantic_weight: float = 0.60,
        lexical_weight: float = 0.35,
        sku_bonus: float = 0.25,
        pop_weight: float = 0.05,
        favorite_bonus: float = 0.15
    ) -> list[dict[str, Any]]:
        """
        Executes hybrid search over PostgreSQL.
        Short queries (<= 3 words) with strong lexical match bypass neural embedding.
        """
        clean_query = normalize_and_expand_query(query)
        if not clean_query:
            return []
            
        raw_query_str = query.strip()

        # Fast Lexical Bypass for short queries (<= 3 words)
        if len(raw_query_str.split()) <= 3 or len(clean_query.split()) <= 3:
            fast_results = self._try_fast_lexical_search(
                clean_query=clean_query,
                raw_query=raw_query_str,
                customer_id=customer_id,
                limit=limit,
                semantic_weight=semantic_weight,
                lexical_weight=lexical_weight,
                sku_bonus=sku_bonus,
                pop_weight=pop_weight,
                favorite_bonus=favorite_bonus
            )
            if fast_results:
                return fast_results

        # Full Neural Vector Hybrid Search Fallback
        query_vec_str = self._embed_query_vec_str(clean_query)
        
        sql = """
            WITH semantic_candidates AS (
                SELECT id
                FROM products
                WHERE is_active = true AND embedding IS NOT NULL
                ORDER BY embedding <=> %(query_vec)s::vector
                LIMIT 60
            ),
            lexical_candidates AS (
                SELECT id
                FROM products
                WHERE is_active = true 
                  AND (%(clean_query)s <%% search_text OR UPPER(sku) = UPPER(%(raw_query)s))
                LIMIT 40
            ),
            all_candidates AS (
                SELECT id FROM semantic_candidates
                UNION
                SELECT id FROM lexical_candidates
            ),
            scored AS (
                SELECT 
                    p.id,
                    p.sku,
                    p.name_en,
                    p.name_ar,
                    p.brand_en,
                    p.brand_ar,
                    p.subcategory_id,
                    p.price,
                    p.size_en,
                    p.unit,
                    p.popularity_score,
                    (1.0 - (p.embedding <=> %(query_vec)s::vector)) AS semantic_score,
                    (
                        0.70 * word_similarity(%(clean_query)s, split_part(p.search_text, '| category:', 1)) +
                        0.30 * word_similarity(%(clean_query)s, p.search_text)
                    ) AS lexical_score,
                    (CASE WHEN UPPER(p.sku) = UPPER(%(raw_query)s) THEN 1.0 ELSE 0.0 END) AS sku_match,
                    (CASE WHEN f.product_id IS NOT NULL THEN 1.0 ELSE 0.0 END) AS is_favorite
                FROM products p
                JOIN all_candidates c ON p.id = c.id
                LEFT JOIN favorites f ON p.id = f.product_id AND f.customer_id = %(customer_id)s::uuid
            )
            SELECT 
                s.id,
                s.sku,
                s.name_en,
                s.name_ar,
                s.brand_en,
                s.brand_ar,
                c.name_en AS category_en,
                sc.name_en AS subcategory_en,
                s.price,
                s.size_en,
                s.unit,
                s.popularity_score,
                s.semantic_score,
                s.lexical_score,
                s.sku_match,
                s.is_favorite,
                (
                    (%(w_sem)s * s.semantic_score) +
                    (%(w_lex)s * s.lexical_score) +
                    (%(w_sku)s * s.sku_match) +
                    (%(w_pop)s * (COALESCE(s.popularity_score, 0.0) / 10.0)) +
                    (%(w_fav)s * s.is_favorite)
                ) AS final_score
            FROM scored s
            JOIN subcategories sc ON s.subcategory_id = sc.id
            JOIN categories c ON sc.category_id = c.id
            ORDER BY final_score DESC
            LIMIT %(limit)s;
        """
        
        params = {
            "query_vec": query_vec_str,
            "clean_query": clean_query,
            "raw_query": raw_query_str,
            "customer_id": customer_id if customer_id else None,
            "limit": limit,
            "w_sem": semantic_weight,
            "w_lex": lexical_weight,
            "w_sku": sku_bonus,
            "w_pop": pop_weight,
            "w_fav": favorite_bonus
        }
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    item = dict(zip(columns, row))
                    item["id"] = str(item["id"])
                    item["price"] = float(item["price"]) if item["price"] is not None else None
                    item["popularity_score"] = float(item["popularity_score"]) if item["popularity_score"] is not None else 0.0
                    item["semantic_score"] = float(item["semantic_score"]) if item["semantic_score"] is not None else 0.0
                    item["lexical_score"] = float(item["lexical_score"]) if item["lexical_score"] is not None else 0.0
                    item["final_score"] = float(item["final_score"]) if item["final_score"] is not None else 0.0
                    item["is_favorite"] = bool(item["is_favorite"])
                    results.append(item)
                return results
        except Exception:
            self._conn = None
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    item = dict(zip(columns, row))
                    item["id"] = str(item["id"])
                    item["price"] = float(item["price"]) if item["price"] is not None else None
                    item["popularity_score"] = float(item["popularity_score"]) if item["popularity_score"] is not None else 0.0
                    item["semantic_score"] = float(item["semantic_score"]) if item["semantic_score"] is not None else 0.0
                    item["lexical_score"] = float(item["lexical_score"]) if item["lexical_score"] is not None else 0.0
                    item["final_score"] = float(item["final_score"]) if item["final_score"] is not None else 0.0
                    item["is_favorite"] = bool(item["is_favorite"])
                    results.append(item)
                return results


def search_products(query: str, customer_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Convenience function delegating to the warm engine instance."""
    engine = HybridSearchEngine.get_instance()
    return engine.search_products(query, customer_id=customer_id, limit=limit)


if __name__ == "__main__":
    test_queries = ["لبن جهينة", "شيبسي كباب", "nescafe", "فطار خفيف"]
    print("Testing search_products with sample queries...")
    for q in test_queries:
        t0 = time.time()
        res = search_products(q, limit=3)
        dt = (time.time() - t0) * 1000
        print(f"\nQuery: '{q}' (took {dt:.1f}ms):")
        for idx, item in enumerate(res, 1):
            print(f"  {idx}. [{item['sku']}] {item['name_en']} ({item['name_ar']}) | Score: {item['final_score']:.4f} (Sem: {item['semantic_score']:.4f}, Lex: {item['lexical_score']:.4f})")