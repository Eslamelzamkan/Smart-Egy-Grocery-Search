# 🛒 Egyptian Grocery Search

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.1-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW-blue)](https://github.com/pgvector/pgvector)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A fast, practical search engine built natively inside PostgreSQL that understands how Egyptians actually shop for groceries—whether they type in local slang (*"قوطة"*), Franco-Arab (*"gehina laban"*), or by meal occasion (*"سحور رمضان"*).

---

## Why This Exists

If you order groceries online in Egypt, you've probably searched for **"قوطة"** (tomatoes) or **"gehina laban"** (Juhayna milk) and gotten `0 Products Found`. 

The store has plenty in stock, but their database lists them formally as *"طماطم طازجة"* and *"حليب جهينة"*. Standard SQL search (`ILIKE`) only looks for exact letter matches, so it fails completely on slang, typos, and Franco-Arab. 

In our tests across 100 everyday Egyptian grocery searches, **67% of standard SQL searches returned zero results.**

---

## How We Fixed It (Without Elasticsearch)

Instead of spinning up a separate, heavy search server and dealing with data-sync headaches, everything runs inside a **single PostgreSQL query** in under 150ms on a normal CPU:

1. **Text Cleanup (`arabic_english_text_normalizer.py`):** Converts Franco-Arab to Arabic (`3esh` → `عيش`), maps local slang (`قوطة` → `طماطم`), and standardizes tricky Arabic letters (like `أ/إ/آ` and `ه/ة`).
2. **Meaning Search (`pgvector`):** Uses `multilingual-e5-large` embeddings so searches like *"مقادير كيكة"* (cake ingredients) bring up flour, sugar, and vanilla.
3. **Typo Tolerance (`pg_trgm`):** Catches misspelled words and partial brand names in under 2ms.
4. **Popularity Boost:** Ranks everyday staples (like fresh milk) above niche items (like almond milk powder) based on actual past orders.
5. **Fast Exact Match:** If someone types a clear, exact brand name, it skips the AI model entirely and returns results in `< 5ms`.

---



## How the Ranking Formula Works

When a user searches, PostgreSQL grabs the top matches from the vector index and the trigram index, filters out out-of-stock items (`WHERE is_active = true`), and scores them using a simple weighted formula:

```text
Final Score = (0.55 × Meaning Match) + (0.35 × Spelling Match) + (0.10 × Popularity Score)
```

---

## Quick Start

### 1. Requirements

* PostgreSQL 18 (with `pgvector` and `pg_trgm` installed)
* Python 3.10+

### 2. Install

```bash
git clone https://github.com/Eslamelzamkan/Smart-Egy-Grocery-Search.git
cd Smart-Egy-Grocery-Search

python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set Up the Database

Add your database credentials to `.env`:

```bash
cp .env.example .env
```

Enable the extensions, calculate product popularity, and generate the vector embeddings:

```bash
psql -d product_ai_training -f sql/01_enable_pgvector_and_trgm_extensions.sql
psql -d product_ai_training -f sql/02_compute_product_popularity_scores.sql
python src/build_product_embeddings_index.py
```

### 4. Run the App or Benchmarks

Launch the Streamlit UI to test searches side-by-side:

```bash
streamlit run demo_web_ui.py
```

Or run the 100-query benchmark script:

```bash
python benchmarks/run_recall_mrr_latency_evaluation.py
```

---

## Repo Layout

```text
├── sql/          # SQL scripts for pgvector/pg_trgm setup and popularity scoring
├── src/          # Text normalizer, embedding generator, and main search query
├── benchmarks/   # 100 test queries (CSV) and evaluation script
├── docs/         # Deeper dives into schema design and benchmark breakdowns
└── demo_web_ui.py # Side-by-side Streamlit demo
```

---

## License

[MIT](LICENSE)
