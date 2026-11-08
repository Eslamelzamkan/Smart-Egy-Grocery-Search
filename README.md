# 🛒 Smart Egyptian Grocery Search (محرك البحث الذكي للمنتجات)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.1-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW_Cosine-blue)](https://github.com/pgvector/pgvector)
[![pg_trgm](https://img.shields.io/badge/pg__trgm-GIN_Lexical-orange)](https://www.postgresql.org/docs/current/pgtrgm.html)
[![Model](https://img.shields.io/badge/Model-multilingual--e5--large-purple)](https://huggingface.co/intfloat/multilingual-e5-large)
[![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A real-world, single-query hybrid search engine that understands how Egyptians actually search for groceries—handling local slang (*"قوطة"*), Franco-Arab (*"gehina laban"*), and recipe occasions (*"سحور رمضان"*) with sub-150ms p95 latency on standard CPU.**

---

## 💡 The Real-World Problem: "We Have It in Stock, So Why 0 Results?"

If you've ever ordered groceries online in Egypt, you've probably hit this frustrating wall:

You type **"قوطة"** (the everyday Egyptian dialect for tomatoes), or **"gehina laban"** (Franco-Arab), and the app proudly tells you:
```text
🔍 "0 Products Found"
```
The store's warehouse has hundreds of kilograms of fresh tomatoes and crates of Juhayna milk. But the product catalog lists them as *"طماطم طازجة"* and *"حليب جهينة"*. Because the app uses standard database keyword matching (`ILIKE '%قوطة%'`), it returns nothing. 

The customer assumes the item is sold out, abandons the cart, and orders from a competitor.

In our baseline benchmark across realistic Egyptian grocery queries:
- **67% of searches resulted in complete dead ends (0 results).**
- Common typos, missing dots (*ه* vs *ة*), and Latin Franco spelling completely broke the catalog.
- Recipe queries like *"سحور رمضان"* (Ramadan Suhoor staples) or *"مقادير كيكة"* (baking essentials) failed entirely.

---

## 🎯 What We Built

Instead of setting up and maintaining a separate, heavyweight search cluster (like Elasticsearch) with data sync lag and dual-write headaches, we built a **single-query hybrid search engine natively inside PostgreSQL 18**:

1. **Dialect & Franco Normalizer:** Translates Egyptian Franco (`gehina` ➔ `جهينة`, `3esh` ➔ `عيش`), maps colloquial terms (`قوطة` ➔ `طماطم`), and unifies tricky Arabic spelling variations (Alefs, Teh Marbuta, Tashkeel).
2. **Dense Semantic Embeddings:** 1024-dimensional vectors from `intfloat/multilingual-e5-large` with **HNSW Cosine indexing** for intent and conceptual matches.
3. **Fuzzy Trigram Matching:** Native `pg_trgm` GIN index with `word_similarity` to catch misspellings and partial brand names in < 2ms.
4. **Bayesian Popularity Re-ranking:** Prioritizes products with verified purchase history and high repeat orders so popular staples rank higher than niche variants.
5. **Fast Lexical Bypass:** Clear exact-match queries (e.g. typing a short, distinct brand name) bypass embedding generation entirely and return in < 5ms.

---

## 📊 Before vs. After: Benchmark on 100 Golden Queries

We curated a 100-query benchmark dataset representing real customer habits across 4 distinct categories:
- **Colloquial Slang & Synonyms** (*"قوطة"*, *"عيش بلدي"*, *"شيبسي كباب"*)
- **Franco-Arab & Transliteration** (*"gehina laban"*, *"makrona penne"*, *"chipsy"*)
- **Recipe & Meal Occasions** (*"سحور رمضان"*, *"مقادير صينية كيكة"*, *"فطار سريع"*)
- **Typos & Orthographic Variations** (missing hamzas, dots, informal spelling)

| Metric | Baseline (`SQL ILIKE`) | Smart Hybrid Engine | Real-World Impact |
| :--- | :---: | :---: | :---: |
| **Zero-Results Rate (Dead Ends)** | **67.0%** | **0.0%** | **Eliminated 100% of empty search screens** |
| **Recall@5** | 33.0% | **86.0%** | **+160.6% increase in finding target products** |
| **MRR@5 (Ranking Quality)** | 0.287 | **0.781** | **Relevant item lands in Top-2 positions** |
| **p95 Latency (Warm CPU)** | 1.9 ms | **132.1 ms** | **Sub-150ms user experience on plain CPU** |

### 🔍 Real Query Examples

| Customer Query | What They Meant | Baseline SQL | Smart Hybrid Engine |
| :--- | :--- | :---: | :--- |
| **`قوطة`** | Fresh Tomatoes | ❌ *0 found* | 🥇 **طماطم طازجة فرز أول** (#1) |
| **`gehina laban`** | Juhayna Milk (Franco) | ❌ *0 found* | 🥇 **حليب جهينة كامل الدسم 1 لتر** (#1) |
| **`سحور رمضان`** | Ramadan Suhoor bundle | ❌ *0 found* | 🥇 **فول مدمس، جبنة فيتا، بيض، زبادي بلدي** |
| **`شيبسي كباب`** | Kebab Chips | ❌ *0 found* | 🥇 **شيبسي بنكهة الكباب المتبل** (#1) |
| **`مقادير كيكة`** | Cake Baking Ingredients | ❌ *0 found* | 🥇 **دقيق، سكر، بيكنج بودر، فانيليا** |

---

## 🛠️ How It Works (The Pipeline)

```
                       User Types Query
        ("قوطة" / "gehina laban" / "سحور رمضان")
                          │
                          ▼
        ┌───────────────────────────────────┐
        │ 1. Egyptian Arabic & Franco Map  │
        │ - Strip Tashkeel & Tatweel        │
        │ - Unify Alef & Teh Marbuta        │
        │ - Transliterate Franco terms      │
        │ - Expand colloquial synonyms      │
        └─────────────────┬─────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    Dense Vector (1024-d)       Lexical Trigrams
  (multilingual-e5-large)      (pg_trgm GIN index)
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────────┐
  │         2. PostgreSQL 18.1 Single Query          │
  │                                                  │
  │ Candidate CTE:                                   │
  │ - 120 vector candidates via HNSW (< 4ms)         │
  │ - 50 lexical candidates via GIN (< 2ms)          │
  │                                                  │
  │ Composite Score:                                 │
  │   0.55 * Vector_Cosine_Similarity                │
  │ + 0.35 * Trigram_Word_Similarity                 │
  │ + 0.10 * Logarithmic_Popularity_Score            │
  │                                                  │
  │ Filter: WHERE is_active = true                   │
  └───────────────────────┬──────────────────────────┘
                          │
                          ▼
            Clean, Ranked Product Cards
             Returned to User (< 135ms)
```

### Why Do We Include Popularity?
A search for *"لبن"* (milk) shouldn't return obscure powdered milk cans or almond milk ahead of staple fresh milk just because of word overlap. We compute a logarithmic Bayesian popularity score based on verified completed customer orders and wishlist saves. This ensures high-velocity household staples naturally bubble to the top.

---

## 📂 Project Structure

```text
├── sql/
│   ├── 01_enable_pgvector_and_trgm_extensions.sql # Extension installs & HNSW/GIN index creation
│   └── 02_compute_product_popularity_scores.sql   # Bayesian sales & wishlist popularity score script
├── src/
│   ├── arabic_english_text_normalizer.py          # Egyptian dialect cleaner, Franco mapper & enrichment
│   ├── build_product_embeddings_index.py          # Multilingual-e5-large vector generation pipeline
│   └── hybrid_product_search_engine.py            # Production single-query hybrid search engine
├── benchmarks/
│   ├── egyptian_grocery_golden_100_queries.csv    # 100 ground-truth queries mapped to verified product IDs
│   ├── run_recall_mrr_latency_evaluation.py       # Benchmark test runner (Baseline vs. Hybrid)
│   └── evaluation_detailed_results.json           # Raw query-by-query benchmark results
├── docs/
│   ├── search_benchmark_comparison_report.md      # Detailed benchmark analysis & category breakdowns
│   ├── postgres_database_schema_report.md         # Database schema audit and data profile
│   └── internship_executive_presentation_report.md# Executive technical summary
├── demo_web_ui.py                                 # Streamlit interactive comparison interface
├── .env.example                                   # Sample environment configuration
├── requirements.txt                               # Python dependencies
├── LICENSE                                        # MIT License
└── README.md
```

---

## ⚡ Getting Started

### 1. Prerequisites
- **PostgreSQL 18** (with `pgvector` and `pg_trgm` extensions enabled)
- **Python 3.10+**

### 2. Setup Your Environment
```bash
# Clone the repository
git clone https://github.com/Eslamelzamkan/Smart-Egy-Grocery-Search.git
cd Smart-Egy-Grocery-Search

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database & Config
Copy `.env.example` to `.env` and enter your PostgreSQL credentials:
```bash
cp .env.example .env
```

Run the database setup scripts:
```bash
psql -d product_ai_training -f sql/01_enable_pgvector_and_trgm_extensions.sql
psql -d product_ai_training -f sql/02_compute_product_popularity_scores.sql
```

Generate product embeddings and build the HNSW index:
```bash
python src/build_product_embeddings_index.py
```

### 4. Try the Interactive Web Demo
Launch the side-by-side Streamlit UI to test queries interactively:
```bash
streamlit run demo_web_ui.py
```

### 5. Reproduce the Benchmark
Run all 100 Golden Queries to verify Recall@5, MRR@5, and Latency:
```bash
python benchmarks/run_recall_mrr_latency_evaluation.py
```

---

## 🔒 Production Safety & Principles

- **No Zombie Products:** Strictly enforces `WHERE is_active = true`—deactivated or out-of-stock items never appear in results.
- **Symmetric Normalization:** Both indexed text and search queries go through the exact same normalization pipeline so there are no representation mismatches.
- **SQL Injection Proof:** 100% parameterized queries using `psycopg` placeholders.
- **Zero Raw UUID/JSON Leaks:** Clean, human-readable product cards built for real store users.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
