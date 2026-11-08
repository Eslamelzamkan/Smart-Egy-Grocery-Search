# Egyptian Grocery Smart Product Search: Agent Architecture & Workspace Guide

Welcome to the **Egyptian Grocery Smart Product Search** project (`product_ai_training` on PostgreSQL 18.1 at `localhost:5432`).

For full schema analysis, table relationships, and data profiles, refer to:
- [PostgreSQL Database Schema Report](docs/postgres_database_schema_report.md)

---

## Workspace Directory Structure

```text
.
├── .agents/
│   ├── rules/
│   │   └── egyptian_arabic_and_sql_safety_rules.md      # Active filter, normalization, parameterized SQL & warm latency rules
│   └── skills/
│       ├── ponytail/                                    # Minimalist senior developer coding discipline
│       │   └── SKILL.md
│       ├── normalize-arabic-and-build-golden-dataset/   # Stage 1: audit, text normalization, popularity scores, golden dataset
│       │   └── SKILL.md
│       ├── build-pgvector-trigram-hybrid-search/        # Stage 2: E5 embeddings, HNSW + GIN indexing, hybrid ranking engine
│       │   └── SKILL.md
│       ├── evaluate-search-recall-mrr-and-latency/      # Stage 3: evaluation suite, baseline vs hybrid comparison, latency
│       │   └── SKILL.md
│       └── clean-streamlit-search-ui/                   # Stage 4: clean, executive Streamlit search comparison interface
│           └── SKILL.md
├── sql/
│   ├── 01_enable_pgvector_and_trgm_extensions.sql       # Vector & pg_trgm extensions, products schema alter
│   └── 02_compute_product_popularity_scores.sql         # Logarithmic delivered orders + favorites popularity score
├── src/
│   ├── arabic_english_text_normalizer.py                # Egyptian Arabic and English text normalizer & enricher
│   ├── build_product_embeddings_index.py                # Multilingual-e5-large embeddings generation & DB indexing
│   └── hybrid_product_search_engine.py                  # Single-query hybrid search engine (semantic + trigram + popularity)
├── benchmarks/
│   ├── egyptian_grocery_golden_100_queries.csv          # 100 Golden Queries mapped to real product IDs across 4 buckets
│   └── run_recall_mrr_latency_evaluation.py             # Benchmark script comparing ILIKE baseline vs Hybrid engine
├── docs/
│   ├── postgres_database_schema_report.md               # Complete schema audit with row counts and sample JSON
│   └── search_benchmark_comparison_report.md            # Comprehensive performance & accuracy evaluation report
├── demo_web_ui.py                                       # Stage 4 Stakeholder comparison web UI (Streamlit)
├── .env                                                 # Database and model configuration
└── AGENTS.md                                            # Project architecture and instructions
```

---

## Ponytail Discipline & Workflow Execution

Agents operating in this repository adhere to the **Ponytail** minimalist coding discipline:
- **Read, then climb:** Inspect real PostgreSQL schemas and live catalog data before writing code.
- **Safety Floors:** Always filter `WHERE p.is_active = true`, normalize queries and index identically, use parameterized queries, and maintain warm model latency `< 150ms`.
- **Native SQL first:** Leverage PostgreSQL 18 native features (`pgvector`, `pg_trgm`, `HNSW`, `GIN`) to do heavy lifting in a single query.
