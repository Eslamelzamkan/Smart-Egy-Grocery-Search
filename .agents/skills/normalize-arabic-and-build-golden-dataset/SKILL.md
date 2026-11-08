---
name: normalize-arabic-and-build-golden-dataset
description: Stage 1 workflow for auditing grocery catalog, applying Arabic/English text normalization, enriching search_text, computing Bayesian-style logarithmic popularity scores, and building the 100-query Golden Dataset CSV.
---

# Stage 1: Normalize Arabic & Build Golden Dataset

## Objectives
1. **Catalog Audit:** Inspect PostgreSQL database schema and sample rows from `products`, `categories`, `subcategories`, `orders`, `order_items`, and `favorites`.
2. **Schema Enhancements:**
   - Enable `vector` and `pg_trgm` extensions.
   - Add `search_text text`, `popularity_score numeric DEFAULT 0`, and `embedding vector(1024)` to `products`.
3. **Popularity Scoring:**
   - Compute `popularity_score = LN(1 + total_delivered_orders + (total_favorites * 2))` from delivered orders and customer wishlists.
4. **Rich Egyptian Arabic Normalizer:**
   - Build normalizer stripping Tashkeel & Tatweel, unifying Alef/Teh Marbuta/Alef Maksura, and lowercasing English/Franco.
   - Populate `products.search_text` using:
     `[name_en] | [name_ar] | Brand: [brand_en] [brand_ar] | Category: [category_en] [category_ar] > [subcategory_en] [subcategory_ar] | Size: [size_en] [size_ar] [unit]`.
5. **Golden Dataset:**
   - Create `benchmarks/egyptian_grocery_golden_100_queries.csv` with 100 queries across 4 buckets:
     - `direct_bilingual` (e.g. "milk", "لبن جهينة")
     - `egyptian_slang` (e.g. "شيبسي كباب", "جبنة رومي قديمة")
     - `franco_and_typos` (e.g. "gehina", "جبنه", "nescafe")
     - `intent_concept` (e.g. "فطار خفيف", "سحور رمضان", "تنظيف البيت")
   - Map each query to verified ground truth `product_id`s existing in the catalog.
