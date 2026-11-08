---
trigger: always_on
description: Hard constraints for SQL queries, Arabic normalization, and search ranking
---

# Egyptian Arabic & SQL Safety Rules

All search features, SQL scripts, and API services in this project must strictly comply with the following mandatory safety and accuracy rules:

## 1. Active Products Filter
- Always filter active products: `WHERE p.is_active = true` (or alias equivalent). Inactive or archived products must NEVER be returned in customer search results.

## 2. Identical Egyptian Arabic Normalization
Both indexed `search_text` and incoming user queries MUST pass through the exact same normalization function:
- Strip Tashkeel (diacritics: `[\u064B-\u065F\u0670]`).
- Strip Tatweel (`ـ` / `\u0640`).
- Unify Alef variants: `أ`, `إ`, `آ` -> `ا`.
- Unify Teh Marbuta: `ة` -> `ه`.
- Unify Alef Maksura / Yeh: `ى` -> `ي`.
- Lowercase all Latin text (English and Franco-Arab: e.g. `Juhayna` -> `juhayna`, `laban` -> `laban`).
- Collapse multiple whitespace characters into a single space and strip leading/trailing spaces.

## 3. Parameterized SQL Queries (SQL Injection Prevention)
- Always use parameterized queries with `psycopg` (e.g. `%(query)s`, `%(customer_id)s`, `%s`).
- NEVER format raw user inputs directly into SQL strings using f-strings or string concatenation.

## 4. In-Memory Warm Model Latency Floor
- Search latency floor: warm search p95 latency must stay `< 150ms`.
- Keep the embedding model (`intfloat/multilingual-e5-large`) loaded and warm in memory (singleton pattern); never reload model weights per query.
