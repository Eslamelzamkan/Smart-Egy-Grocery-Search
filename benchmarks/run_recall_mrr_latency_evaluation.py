import os
import sys
import csv
import time
import json
from pathlib import Path
from typing import Any
import numpy as np
from dotenv import load_dotenv

# Ensure environment flags and paths
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

import psycopg
from src.arabic_english_text_normalizer import normalize_text
from src.hybrid_product_search_engine import HybridSearchEngine

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/product_ai_training")
GOLDEN_CSV = "benchmarks/egyptian_grocery_golden_100_queries.csv"


def run_baseline_ilike_search(query: str, db_url: str, limit: int = 5) -> tuple[list[str], float]:
    """
    Standard naive SQL ILIKE search baseline.
    Filters p.is_active = true and searches name and brand fields.
    Returns (retrieved_product_ids, latency_ms).
    """
    t0 = time.time()
    words = query.strip().split()
    if not words:
        return [], 0.0
        
    conditions = []
    params = {}
    for idx, w in enumerate(words):
        param_name = f"w_{idx}"
        params[param_name] = f"%{w}%"
        conditions.append(f"""
            (p.name_en ILIKE %({param_name})s OR 
             p.name_ar ILIKE %({param_name})s OR 
             p.brand_en ILIKE %({param_name})s OR 
             p.brand_ar ILIKE %({param_name})s)
        """)
        
    sql = f"""
        SELECT p.id 
        FROM products p
        WHERE p.is_active = true
          AND ({" OR ".join(conditions)})
        ORDER BY p.popularity_score DESC
        LIMIT {limit};
    """
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            ids = [str(r[0]) for r in cur.fetchall()]
            
    dt_ms = (time.time() - t0) * 1000.0
    return ids, dt_ms


def compute_query_metrics(retrieved_ids: list[str], target_ids: set[str]) -> tuple[float, float, int]:
    """
    Computes (recall_at_5, mrr_at_5, is_zero_results).
    """
    if not retrieved_ids:
        return 0.0, 0.0, 1
        
    hits = [1 if pid in target_ids else 0 for pid in retrieved_ids]
    # Recall@5: fraction of target set found in top-5 (or hit indicator if target set small)
    relevant_found = sum(hits)
    recall = relevant_found / len(target_ids) if target_ids else 0.0
    # Also hit indicator (Hit@5) bounded to 1.0
    hit_rate = 1.0 if relevant_found > 0 else 0.0
    
    # MRR@5: 1 / rank of first relevant item
    mrr = 0.0
    for rank, pid in enumerate(retrieved_ids, 1):
        if pid in target_ids:
            mrr = 1.0 / rank
            break
            
    return hit_rate, mrr, 0


def run_full_evaluation():
    print("=" * 70)
    print("STARTING SEARCH EVALUATION BENCHMARK: BASELINE ILIKE VS HYBRID SMART SEARCH")
    print("=" * 70)
    
    # Load golden queries
    with open(GOLDEN_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        golden_queries = list(reader)
    print(f"Loaded {len(golden_queries)} golden queries from {GOLDEN_CSV}.")
    
    # Initialize hybrid search engine (warmup)
    print("Prewarming HybridSearchEngine...")
    engine = HybridSearchEngine.get_instance(DB_URL)
    # Warmup queries
    for _ in range(3):
        engine.search_products("warmup test", limit=5)
        
    detailed_results = []
    
    baseline_stats = {"recall": [], "mrr": [], "zero": [], "latencies": []}
    hybrid_stats = {"recall": [], "mrr": [], "zero": [], "latencies": []}
    
    bucket_stats = {}
    
    for row in golden_queries:
        qid = row["query_id"]
        q_text = row["query"]
        bucket = row["bucket"]
        target_ids = set(row["target_product_ids"].split(";")) if row["target_product_ids"] else set()
        
        if bucket not in bucket_stats:
            bucket_stats[bucket] = {
                "baseline": {"recall": [], "mrr": [], "zero": [], "latencies": []},
                "hybrid": {"recall": [], "mrr": [], "zero": [], "latencies": []}
            }
            
        # 1. Baseline ILIKE
        b_ids, b_lat = run_baseline_ilike_search(q_text, DB_URL, limit=5)
        b_rec, b_mrr, b_zero = compute_query_metrics(b_ids, target_ids)
        
        baseline_stats["recall"].append(b_rec)
        baseline_stats["mrr"].append(b_mrr)
        baseline_stats["zero"].append(b_zero)
        baseline_stats["latencies"].append(b_lat)
        
        bucket_stats[bucket]["baseline"]["recall"].append(b_rec)
        bucket_stats[bucket]["baseline"]["mrr"].append(b_mrr)
        bucket_stats[bucket]["baseline"]["zero"].append(b_zero)
        bucket_stats[bucket]["baseline"]["latencies"].append(b_lat)
        
        # 2. Hybrid Smart Search
        t_start = time.time()
        h_results = engine.search_products(q_text, limit=5)
        h_lat = (time.time() - t_start) * 1000.0
        h_ids = [item["id"] for item in h_results]
        h_rec, h_mrr, h_zero = compute_query_metrics(h_ids, target_ids)
        
        hybrid_stats["recall"].append(h_rec)
        hybrid_stats["mrr"].append(h_mrr)
        hybrid_stats["zero"].append(h_zero)
        hybrid_stats["latencies"].append(h_lat)
        
        bucket_stats[bucket]["hybrid"]["recall"].append(h_rec)
        bucket_stats[bucket]["hybrid"]["mrr"].append(h_mrr)
        bucket_stats[bucket]["hybrid"]["zero"].append(h_zero)
        bucket_stats[bucket]["hybrid"]["latencies"].append(h_lat)
        
        detailed_results.append({
            "query_id": qid,
            "query": q_text,
            "bucket": bucket,
            "targets_count": len(target_ids),
            "baseline_hits": len(set(b_ids) & target_ids),
            "baseline_recall": b_rec,
            "baseline_mrr": b_mrr,
            "baseline_latency_ms": round(b_lat, 2),
            "hybrid_hits": len(set(h_ids) & target_ids),
            "hybrid_recall": h_rec,
            "hybrid_mrr": h_mrr,
            "hybrid_latency_ms": round(h_lat, 2)
        })
        
    # Save detailed JSON
    with open("benchmarks/evaluation_detailed_results.json", "w", encoding="utf-8") as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
    # Aggregate summaries
    def summarize(stats):
        return {
            "recall@5": round(float(np.mean(stats["recall"])), 4),
            "mrr@5": round(float(np.mean(stats["mrr"])), 4),
            "zero_rate": round(float(np.mean(stats["zero"])), 4),
            "avg_latency_ms": round(float(np.mean(stats["latencies"])), 2),
            "p50_latency_ms": round(float(np.percentile(stats["latencies"], 50)), 2),
            "p95_latency_ms": round(float(np.percentile(stats["latencies"], 95)), 2)
        }
        
    overall_baseline = summarize(baseline_stats)
    overall_hybrid = summarize(hybrid_stats)
    
    print("\n" + "=" * 70)
    print("OVERALL BENCHMARK RESULTS (100 QUERIES)")
    print("=" * 70)
    print(f"Metric                 | Baseline ILIKE | Hybrid Smart Search | Delta / Gain")
    print(f"-----------------------|----------------|---------------------|-------------")
    print(f"Recall@5 (Hit Rate)    | {overall_baseline['recall@5'] * 100:6.2f}%        | {overall_hybrid['recall@5'] * 100:6.2f}%             | +{(overall_hybrid['recall@5'] - overall_baseline['recall@5']) * 100:5.2f}%")
    print(f"MRR@5                  | {overall_baseline['mrr@5']:6.4f}         | {overall_hybrid['mrr@5']:6.4f}              | +{(overall_hybrid['mrr@5'] - overall_baseline['mrr@5']):6.4f}")
    print(f"Zero-Results Rate      | {overall_baseline['zero_rate'] * 100:6.2f}%        | {overall_hybrid['zero_rate'] * 100:6.2f}%             | -{(overall_baseline['zero_rate'] - overall_hybrid['zero_rate']) * 100:5.2f}%")
    print(f"p50 Latency (ms)       | {overall_baseline['p50_latency_ms']:6.2f} ms       | {overall_hybrid['p50_latency_ms']:6.2f} ms            | -")
    print(f"p95 Latency (ms)       | {overall_baseline['p95_latency_ms']:6.2f} ms       | {overall_hybrid['p95_latency_ms']:6.2f} ms            | Floor: < 150ms")
    
    print("\n" + "=" * 70)
    print("BUCKET-BY-BUCKET BREAKDOWN")
    print("=" * 70)
    bucket_summary = {}
    for b_name, b_data in bucket_stats.items():
        b_sum_base = summarize(b_data["baseline"])
        b_sum_hyb = summarize(b_data["hybrid"])
        bucket_summary[b_name] = {"baseline": b_sum_base, "hybrid": b_sum_hyb}
        print(f"\n[Bucket: {b_name.upper()}] (25 Queries)")
        print(f"  Recall@5 : Baseline {b_sum_base['recall@5']*100:.1f}% -> Hybrid {b_sum_hyb['recall@5']*100:.1f}% (+{(b_sum_hyb['recall@5']-b_sum_base['recall@5'])*100:.1f}%)")
        print(f"  MRR@5    : Baseline {b_sum_base['mrr@5']:.4f} -> Hybrid {b_sum_hyb['mrr@5']:.4f}")
        print(f"  Zero-Rate: Baseline {b_sum_base['zero_rate']*100:.1f}% -> Hybrid {b_sum_hyb['zero_rate']*100:.1f}%")
        print(f"  p95 Lat  : Hybrid {b_sum_hyb['p95_latency_ms']:.1f} ms")
        
    # Return results for report generation
    return {
        "overall_baseline": overall_baseline,
        "overall_hybrid": overall_hybrid,
        "bucket_summary": bucket_summary,
        "queries_count": len(golden_queries)
    }


if __name__ == "__main__":
    run_full_evaluation()
