---
name: evaluate-search-recall-mrr-and-latency
description: Stage 3 workflow for benchmarking Recall@5, MRR@5, Zero-Results Rate, and p95 Latency against baseline SQL ILIKE search across all 100 Golden Queries.
---

# Stage 3: Evaluate Search Recall, MRR & Latency

## Objectives
1. **Benchmark Suite Execution:**
   - Execute `benchmarks/run_recall_mrr_latency_evaluation.py` across all 100 Golden Queries.
   - Run baseline search: naive `ILIKE` on `name_en`, `name_ar`, `brand_en`, `brand_ar`, `description_en`, `description_ar`.
   - Run hybrid smart search: single SQL query combining semantic cosine + trigram + popularity + favorites.
2. **Key Evaluation Metrics:**
   - `Recall@5`: Percentage of relevant golden products retrieved in top 5.
   - `MRR@5`: Mean Reciprocal Rank for first relevant item in top 5.
   - `Zero-Results Rate`: Fraction of queries returning 0 results.
   - `Latency`: Mean, p50, and p95 execution time. Target: warm p95 `< 150ms`.
3. **Weight Calibration:**
   - Tune semantic vs. lexical vs. popularity weights until Smart Search outperforms baseline across all 4 query buckets (`direct_bilingual`, `egyptian_slang`, `franco_and_typos`, `intent_concept`).
4. **Documentation:**
   - Generate `docs/search_benchmark_comparison_report.md` detailing executive comparison tables, bucket breakdowns, and latency profiles.
