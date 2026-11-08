# 🛒 Smart Egyptian Grocery Search (محرك البحث الذكي للمنتجات)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.1-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW_Cosine-blue)](https://github.com/pgvector/pgvector)
[![pg_trgm](https://img.shields.io/badge/pg__trgm-GIN_Lexical-orange)](https://www.postgresql.org/docs/current/pgtrgm.html)
[![Model](https://img.shields.io/badge/Model-multilingual--e5--large-purple)](https://huggingface.co/intfloat/multilingual-e5-large)
[![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green?logo=python&logoColor=white)](https://www.python.org/)

> **A production-grade, single-query hybrid search engine engineered specifically for Egyptian e-grocery retail. Handles Egyptian slang (*"قوطة"*), Franco-Arab (*"gehina laban"*), recipe intents (*"سحور رمضان"*), and typos with sub-150ms p95 latency.**

---

## 📌 Executive Summary & The Problem

Traditional e-commerce search engines in Egypt rely heavily on literal SQL `LIKE` or basic text matching. In colloquial Egyptian grocery retail, this creates severe customer friction and revenue drop-off:

- **High Zero-Results Rate (67% Dead Ends):** Shoppers frequently search using colloquial Egyptian dialect (*"قوطة"* for tomatoes, *"شيبسي كباب"*), Franco-Arabic transliterations (*"gehina laban"*, *"makrona"*), and recipe occasions (*"سحور رمضان"*, *"مقادير صينية كيكة"*).
- **Lost Revenue:** When a customer searches *"قوطة"* and gets `"0 Products Found"`, they assume the store is out of stock—even when the warehouse has hundreds of kilograms of fresh tomatoes.

### 💡 The Solution
A **PostgreSQL 18 native single-query hybrid search engine** combining:
1. **Dense Semantic Embeddings:** 1024-dimensional vectors via `intfloat/multilingual-e5-large` with HNSW cosine indexing.
2. **Lexical Fuzzy Trigrams:** Fast `pg_trgm` GIN index with word similarity.
3. **Bayesian Popularity Signals:** Prioritizing verified high-frequency delivered grocery staples.
4. **Colloquial Dialect & Franco Normalizer:** Unifies Arabic orthography, maps Egyptian slang, and transliterates Franco-Arab queries on the fly.

---

## 📊 Benchmark Evaluation: Baseline vs. Smart Hybrid Search

Tested across a curated **100-query Golden Dataset** covering:
- **Egyptian Colloquial Slang & Synonyms** (*"قوطة"* ➔ طماطم)
- **Franco-Arab & Transliteration** (*"gehina laban"*, *"chipsy"*)
- **Complex Semantic & Recipe Intents** (*"سحور رمضان"*, *"مقادير صينية كيكة"*)
- **Typos & Informal Orthography** (missing Alef/Tashkeel variants)

| Metric | Baseline (`SQL ILIKE`) | Smart Hybrid Engine | Impact / Relative Gain |
| :--- | :---: | :---: | :---: |
| **Recall@5** | 33.0% | **86.0%** | **+160.6% relative gain** |
| **MRR@5 (Mean Reciprocal Rank)** | 0.287 | **0.781** | **+172.1% rank accuracy** |
| **Zero-Results Rate (Dead Ends)** | 67.0% | **0.0%** | **100% eliminated (0 dead ends)** |
| **p95 Latency (Warm CPU)** | 1.9 ms | **132.1 ms** | **Sub-150ms latency budget met** |

---

## 🏗️ Technical Architecture

```
                     [ Incoming User Query ]
            (Arabic Slang / Franco-Arab / Recipe Intent)
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │      Egyptian Arabic & Franco Normalizer     │
         │  - Strip Tashkeel & Tatweel                  │
         │  - Unify Orthography (أ/إ/آ -> ا, ة -> ه)    │
         │  - Egyptian Slang Mapping (قوطة -> طماطم)    │
         │  - Franco Transliteration (gehina -> جهينة)  │
         └──────────────────────┬───────────────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       [ Dense Vector 1024-d ]       [ Trigram / Lexical ]
     multilingual-e5-large (Query)     GIN Word Similarity
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
    ┌────────────────────────────────────────────────────────┐
    │       PostgreSQL 18.1 Single-Query Hybrid Search       │
    │                                                        │
    │  Score = 0.55 * Vector_Similarity (HNSW <=> Cosine)    │
    │        + 0.35 * Trigram_Similarity (GIN word_sim)      │
    │        + 0.10 * Logarithmic_Popularity_Score           │
    │                                                        │
    │  WHERE p.is_active = true                              │
    └────────────────────────────────────────────────────────┘
                                │
                                ▼
                   Ranked Product Cards to User
```

---

## 📂 Repository Structure

```text
├── .agents/                                    # Workflow specs & safety rules
│   └── rules/egyptian_arabic_and_sql_safety_rules.md
├── sql/
│   ├── 01_enable_pgvector_and_trgm_extensions.sql # Vector & Trigram extension setup
│   └── 02_compute_product_popularity_scores.sql   # Bayesian logarithmic popularity scores
├── src/
│   ├── arabic_english_text_normalizer.py       # Dialect normalizer, slang & Franco mapper
│   ├── build_product_embeddings_index.py       # E5 embeddings generator & DB indexing
│   └── hybrid_product_search_engine.py         # Production hybrid search engine
├── benchmarks/
│   ├── egyptian_grocery_golden_100_queries.csv # Curated 100-query benchmark dataset
│   ├── run_recall_mrr_latency_evaluation.py    # Automated benchmark runner
│   └── evaluation_detailed_results.json        # Detailed query-by-query benchmark results
├── docs/
│   ├── search_benchmark_comparison_report.md   # Comprehensive benchmark comparison report
│   ├── postgres_database_schema_report.md      # Database schema & catalog audit
│   └── internship_executive_presentation_report.md # Executive presentation report
├── demo_web_ui.py                              # Streamlit executive comparison interface
├── .env.example                                # Environment variable template
├── requirements.txt                            # Python dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **PostgreSQL 18+** with `pgvector` and `pg_trgm` extensions installed.
- **Python 3.10+**

### 2. Installation
```bash
git clone https://github.com/Eslamelzamkan/Smart-Egy-Grocery-Search.git
cd Smart-Egy-Grocery-Search

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Database & Environment Setup
Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```bash
cp .env.example .env
```

Apply database migrations:
```bash
psql -d product_ai_training -f sql/01_enable_pgvector_and_trgm_extensions.sql
psql -d product_ai_training -f sql/02_compute_product_popularity_scores.sql
```

Generate product embeddings and build HNSW index:
```bash
python src/build_product_embeddings_index.py
```

### 4. Run the Interactive Streamlit UI
Compare traditional SQL ILIKE search side-by-side with the Smart Hybrid AI Search:
```bash
streamlit run demo_web_ui.py
```

### 5. Run the Benchmark Evaluation Suite
Run all 100 Golden Queries across both engines to reproduce Recall@5, MRR@5, and Latency:
```bash
python benchmarks/run_recall_mrr_latency_evaluation.py
```

---

## 🛡️ Safety & Quality Principles

- **Active Catalog Filter:** Always enforces `WHERE is_active = true` to protect against displaying out-of-stock or archived SKUs.
- **Identical Normalization:** Both indexed text and runtime search queries pass through the exact same normalization pipeline.
- **100% Parameterized SQL:** Immune to SQL injection attacks by strictly using `psycopg` parameterized bindings.
- **Zero Raw UUID/JSON Clutter:** Clean, compact UI presentation designed for retail stakeholders and customers.

---

## 👤 Author
- **Eslam Elzamkan** - [GitHub](https://github.com/Eslamelzamkan)
