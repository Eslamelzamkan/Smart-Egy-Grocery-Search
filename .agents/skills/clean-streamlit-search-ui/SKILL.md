---
name: clean-streamlit-search-ui
description: Best practices and UI patterns for building clean, executive-ready Streamlit search comparison interfaces with Arabic typography, compact cards, and zero raw JSON/UUID clutter.
---

# Clean Streamlit Search UI Standards

This skill defines UI and UX standards for Streamlit-based search engines, comparative demos, and executive dashboards in Egyptian e-commerce / grocery applications.

## 1. Zero Raw JSON / UUID Clutter
- **Never display raw UUIDs** to shoppers, executives, or stakeholders.
  - Bad: `Customer: 65e673c0-5a8a-483b-ae14-4de458a7ce81`
  - Good: `👤 Customer #1 (Dairy, Cheese & Meat Favorites)`
- **Never display raw Python dictionaries or unformatted JSON blobs**.
  - All product metadata must be extracted into cleanly formatted UI typography.
  - Technical diagnostic information belongs inside compact inline badges or optional collapsed expanders.

## 2. Proper Egyptian Arabic Typography & CSS Polish
Always inject custom scoped CSS to ensure right-to-left Arabic readability, clean font scaling, and tight vertical rhythm:
```python
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.ar-text {
    font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
    direction: rtl;
    text-align: right;
    font-weight: 700;
}
.metric-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 4px;
}
.badge-green { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
.badge-gray  { background-color: #f1f3f4; color: #3c4043; border: 1px solid #dadce0; }
.badge-blue  { background-color: #e8f0fe; color: #1a73e8; border: 1px solid #d2e3fc; }
.badge-red   { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
.badge-fav   { background-color: #fef7e0; color: #b06000; border: 1px solid #fdd663; font-weight: 700; }
</style>
""", unsafe_allow_html=True)
```

## 3. Compact Product Cards (`st.container(border=True)`)
Render each product inside a compact, cleanly structured bordered container that displays all relevant attributes without excessive vertical height:
- **Header Line:**
  - `#Rank` badge (e.g. `#1`, `#2`)
  - **Arabic Name (`name_ar`)** prominently displayed with Cairo font
  - **Price (`EGP xx.xx`)** highlighted in green or bold text
- **Sub-Header Line:**
  - English Name (`name_en`)
  - Brand name
  - Size / Unit
  - Category / Subcategory breadcrumb
- **Footer Score Bar (for Smart Search):**
  - Inline badges: `Score: 0.84` • `🧠 Sem: 0.88` • `🔤 Lex: 0.72` • `🔥 Pop: 8.9`

## 4. Single-Screen Executive A/B Comparison Layout
- **Header:** Clean title, subtitle, and an optional collapsible expander (`📊 View 100-Query Benchmark Summary`) to avoid pushing the search controls below the fold.
- **Top Control Bar:**
  - Full-width prominent search bar with intuitive Egyptian examples.
  - Horizontal preset row for immediate single-click demonstration of hard edge cases (Franco-Arabic, slang, meal intent, typos).
- **Side-by-Side Comparison Columns:**
  - Left column: `❌ Baseline: SQL ILIKE` with hit count and query latency.
  - Right column: `✅ Hybrid Smart Search: pgvector + pg_trgm + LTR` with hit count, warm sub-150ms latency pill, and smart scoring tags.
  - When baseline returns 0 results, display an informative, styled alert box explaining why traditional keyword search failed (e.g. spelling variation, franco alias, or semantic gap).
