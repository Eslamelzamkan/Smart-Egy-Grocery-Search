# Egyptian Grocery Smart Product Search: Benchmark Comparison Report

**Database:** `product_ai_training` (PostgreSQL 18.1 at `localhost:5432`)  
**Catalog Size:** 1,093 Products (1,068 active items across 14 categories)  
**Golden Dataset:** 100 Verified Ground-Truth Queries across 4 Archetypes  
**Model:** `intfloat/multilingual-e5-large` (1024-dim, HNSW cosine index + GIN trigram index)  
**Enhancements:** Subcategory Intent / Meal Occasion Tags + Phonetic Franco-Arabic Transliteration  

---

## 1. Executive Summary

A comprehensive benchmark was conducted comparing the **Naive SQL `ILIKE` Baseline** against our **PostgreSQL Hybrid Smart Search Engine** across 100 realistic Egyptian grocery queries.

With the addition of **Subcategory Intent & Usage Occasion Tags** and the **Phonetic Franco-Arabic Transliteration Map**, the search engine reached state-of-the-art retrieval accuracy:

### Key Benchmark Highlights:
- **Recall@5 (Hit Rate):** Jumped from **58.00%** to **86.00%** (**+28.00%** absolute lift, +48.3% relative gain).
- **MRR@5 (Mean Reciprocal Rank):** Surged from **0.4113** to **0.8067** (**+0.3954** absolute lift, **+96.1%** relative rank improvement — target items appear almost exclusively in rank #1 or #2).
- **Franco & Typos Hit Rate:** Reached a perfect **100.0%** Recall@5 with an MRR of **0.9533** (up from 44% baseline).
- **Zero-Results Rate Eliminated:** Dropped from **18.00%** to **0.00%** across the entire golden test suite.
- **Latency Floor Satisfied:** Warm p95 latency clocked in at **132.11 ms**, staying strictly below the `< 150ms` production floor.

---

## 2. Overall Performance Comparison

| Metric | Baseline SQL `ILIKE` | Hybrid Smart Search (Initial) | Hybrid Smart Search (Enriched) | Total Delta vs Baseline |
|---|---|---|---|---|
| **Recall@5 (Hit Rate)** | 58.00% | 75.00% | **86.00%** | **+28.00%** |
| **MRR@5 (Mean Reciprocal Rank)** | 0.4113 | 0.6942 | **0.8067** | **+0.3954** (+96.1%) |
| **Zero-Results Rate** | 18.00% | 0.00% | **0.00%** | **-18.00% (Eliminated)** |
| **p50 Latency (Warm)** | 48.87 ms | 92.15 ms | **119.64 ms** | Dense vector + lexical scoring |
| **p95 Latency (Warm)** | 159.16 ms | 105.75 ms | **132.11 ms** | **Meets `< 150ms` floor** |

---

## 3. Bucket-by-Bucket Breakdown (25 Queries per Bucket)

```mermaid
graph LR
    A["User Query"] --> B{"Query Archetype"}
    B -->|Direct Names| C["Direct Bilingual<br/>Recall: 100% | MRR: 0.9733"]
    B -->|Egyptian Vernacular| D["Egyptian Slang<br/>Recall: 84% | MRR: 0.8200"]
    B -->|Franco & Typos| E["Franco & Typos<br/>Recall: 100% | MRR: 0.9533"]
    B -->|High-Level Intent| F["Intent / Concept<br/>Recall: 60% | MRR: 0.4800"]
```

### Detailed Bucket Metrics Table

| Query Archetype Bucket | Metric | Baseline `ILIKE` | Hybrid (Initial) | Hybrid (Enriched) | Net Gain vs Baseline |
|---|---|---|---|---|---|
| **Direct Bilingual** *(25 queries)* | Recall@5<br/>MRR@5 | 76.0%<br/>0.5047 | 100.0%<br/>0.9200 | **100.0%**<br/>**0.9733** | **+24.0%**<br/>**+0.4686** |
| **Egyptian Slang** *(25 queries)* | Recall@5<br/>MRR@5 | 76.0%<br/>0.4827 | 84.0%<br/>0.7933 | **84.0%**<br/>**0.8200** | **+8.0%**<br/>**+0.3373** |
| **Franco & Typos** *(25 queries)* | Recall@5<br/>MRR@5 | 44.0%<br/>0.3600 | 72.0%<br/>0.6700 | **100.0%**<br/>**0.9533** | **+56.0%**<br/>**+0.5933** |
| **Intent & Concept** *(25 queries)* | Recall@5<br/>MRR@5 | 36.0%<br/>0.2980 | 44.0%<br/>0.3933 | **60.0%**<br/>**0.4800** | **+24.0%**<br/>**+0.1820** |

---

## 4. Analysis of the Key Enhancements

### 1. Subcategory Intent / Meal Occasion Tags
- **Implementation:** In [src/arabic_english_text_normalizer.py](../src/arabic_english_text_normalizer.py), each product's `search_text` is dynamically enriched with contextual Egyptian meal occasions, recipes, and usage patterns:
  - *Cheese / Eggs / Beans / Yogurt:* `Usage: فطار عشاء سحور رمضان سندوتشات breakfast dinner suhoor`
  - *Sugar / Flour / Baking:* `Usage: حلويات مقادير صينية كيكة منزلية خبيز baking cake ingredients desserts`
  - *Cleaners / Bleach / Detergents:* `Usage: تنظيف الحمام والمطبخ والمنزل تعقيم bathroom kitchen cleaning disinfect`
- **Impact:** Intent & Concept Recall jumped from **36% (Baseline) $\rightarrow$ 44% $\rightarrow$ 60%**, surfacing exact household bundles for Suhoor, cake baking, and sanitization.

### 2. Phonetic Franco-to-Arabic Transliteration Map
- **Implementation:** Added lightweight transliteration in [src/arabic_english_text_normalizer.py](../src/arabic_english_text_normalizer.py) (`normalize_and_expand_query`) mapping Egyptian Franco terms (`gehina` $\rightarrow$ `جهينة`, `laban` $\rightarrow$ `لبن`, `3esh` $\rightarrow$ `عيش`, `shepsy` $\rightarrow$ `شيبسي`, `makrona` $\rightarrow$ `مكرونة`, `rumi` $\rightarrow$ `رومي`).
- **Impact:** Franco & Typos Recall skyrocketed from **44% (Baseline) $\rightarrow$ 100.0%**, with MRR reaching **0.9533**. Searches like `gehina laban` now effortlessly retrieve *Juhayna Milk* in rank #1.

### 3. Latency & Candidate Scaling
- Optimized two-stage CTE:
  - 120 top semantic candidates retrieved via HNSW index (< 4 ms).
  - 50 top lexical/SKU candidates retrieved via GIN trigram index (< 2 ms).
  - Linear combination scoring executed on the small candidate union (~120–160 rows) rather than full catalog scan.
- Maintains warm p95 latency at **132.11 ms** on standard CPU.

---

## 5. Artifact Verification Summary

| Component | Path | Status |
|---|---|---|
| Text Normalizer & Franco Map | [arabic_english_text_normalizer.py](../src/arabic_english_text_normalizer.py) | Active with intent tags & Franco transliteration |
| Embeddings & Index Pipeline | [build_product_embeddings_index.py](../src/build_product_embeddings_index.py) | Re-indexed (all 1,093 embeddings updated) |
| Hybrid Search Engine | [hybrid_product_search_engine.py](../src/hybrid_product_search_engine.py) | Active with `normalize_and_expand_query` |
| Benchmark Evaluation Runner | [run_recall_mrr_latency_evaluation.py](../benchmarks/run_recall_mrr_latency_evaluation.py) | Benchmark verified: 86.0% Recall, 0.8067 MRR |
| Detailed Benchmark JSON | [evaluation_detailed_results.json](../benchmarks/evaluation_detailed_results.json) | Full 100-query results logged |
