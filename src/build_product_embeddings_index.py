import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Set environment guards before importing ML libraries
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load database configuration
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import psycopg

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/product_ai_training")
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-base")


def compute_e5_embeddings(texts: list[str], model, tokenizer, batch_size: int = 32, device: str = "cpu"):
    """
    Computes L2-normalized 1024-dim multilingual-e5 embeddings with mean pooling.
    Requires 'passage: ' or 'query: ' prefix.
    """
    all_embeddings = []
    total = len(texts)
    
    for i in range(0, total, batch_size):
        batch_slice = texts[i : i + batch_size]
        # Tokenize with max_length 512
        inputs = tokenizer(
            batch_slice,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            # Mean pooling with attention mask
            token_embeddings = outputs.last_hidden_state
            mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
            sum_embeddings = torch.sum(token_embeddings * mask, dim=1)
            sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
            mean_pooled = sum_embeddings / sum_mask
            # L2 normalization
            normalized_embeddings = F.normalize(mean_pooled, p=2, dim=1)
            all_embeddings.extend(normalized_embeddings.cpu().numpy().tolist())
            
        print(f"  Processed {min(i + batch_size, total)}/{total} embeddings...", flush=True)
        
    return all_embeddings


def build_embeddings_and_indexes():
    """
    Main pipeline:
    1. Fetches all products needing embeddings from PostgreSQL.
    2. Generates 'passage: <search_text>' embeddings using multilingual-e5-large.
    3. Updates products.embedding in batches.
    4. Builds HNSW cosine index and GIN trigram index.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Connecting to database at {DB_URL}...")
    
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            print("Executing safe DDL to resize products.embedding to vector(768)...")
            cur.execute("""
                DROP INDEX IF EXISTS idx_products_embedding_hnsw;
                ALTER TABLE products ALTER COLUMN embedding TYPE vector(768) USING NULL;
            """)
            conn.commit()

            cur.execute("""
                SELECT id, search_text 
                FROM products 
                ORDER BY id;
            """)
            rows = cur.fetchall()
            print(f"Loaded {len(rows)} products for embedding generation.")
            
            p_ids = [r[0] for r in rows]
            # Formulate passage prefix
            passage_texts = [f"passage: {r[1] or ''}" for r in rows]
            
            print(f"Loading tokenizer & model '{MODEL_NAME}' on {device.upper()}...")
            t0 = time.time()
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModel.from_pretrained(MODEL_NAME)
            model.to(device)
            model.eval()
            print(f"Model successfully loaded in {time.time()-t0:.2f}s.")
            
            print("Generating product embeddings...")
            t0 = time.time()
            embeddings = compute_e5_embeddings(passage_texts, model, tokenizer, batch_size=32, device=device)
            print(f"Finished generating {len(embeddings)} embeddings in {time.time()-t0:.2f}s.")
            
            print("Updating products.embedding in PostgreSQL...")
            t0 = time.time()
            update_data = []
            for p_id, emb in zip(p_ids, embeddings):
                # Format as PostgreSQL vector literal string '[v1,v2,...]'
                vec_str = f"[{','.join(f'{x:.6f}' for x in emb)}]"
                update_data.append((vec_str, p_id))
                
            cur.executemany("UPDATE products SET embedding = %s::vector WHERE id = %s;", update_data)
            conn.commit()
            print(f"Successfully stored embeddings for {len(update_data)} products in {time.time()-t0:.2f}s.")
            
            # Step 4: Build HNSW and GIN Indexes
            print("Building PostgreSQL indexes...")
            
            print(" - Creating HNSW cosine index on products.embedding...")
            t_idx = time.time()
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_embedding_hnsw 
                ON products USING hnsw (embedding vector_cosine_ops) 
                WITH (m = 16, ef_construction = 64);
            """)
            conn.commit()
            print(f"   HNSW index ready in {time.time()-t_idx:.2f}s.")
            
            print(" - Creating GIN trigram index on products.search_text...")
            t_idx = time.time()
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_search_text_trgm 
                ON products USING gin (search_text gin_trgm_ops);
            """)
            conn.commit()
            print(f"   GIN trigram index ready in {time.time()-t_idx:.2f}s.")
            
            print(" - Creating B-Tree index on products.sku...")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products (is_active);")
            conn.commit()
            
            print("All vector and trigram indexes are active and ready.")


if __name__ == "__main__":
    build_embeddings_and_indexes()
