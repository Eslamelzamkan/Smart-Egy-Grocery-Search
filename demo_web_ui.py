import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Set paths and environment flags
sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

import streamlit as st
import psycopg

from src.hybrid_product_search_engine import HybridSearchEngine

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/product_ai_training")

# Page Configuration
st.set_page_config(
    page_title="Egyptian Grocery Search — Baseline SQL vs. Hybrid AI Search",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Scoped CSS for Polish & Arabic Typography
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Header typography */
    .main-title {
        font-size: 22px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .main-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: 2px;
        margin-bottom: 12px;
    }
    
    /* Arabic text typography */
    .ar-title {
        font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        direction: rtl;
        text-align: right;
        line-height: 1.4;
    }
    
    /* Column Status Banners */
    .status-banner {
        border-radius: 8px;
        padding: 9px 14px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
    }
    .banner-baseline {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #1e293b;
    }
    .banner-hybrid {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
    }
    
    /* Dead end alert */
    .dead-end-card {
        padding: 28px 16px;
        text-align: center;
        background: #fef2f2;
        border: 1px dashed #f87171;
        border-radius: 8px;
        color: #991b1b;
        margin-top: 8px;
    }
    .dead-end-title {
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .dead-end-desc {
        font-size: 13px;
        color: #7f1d1d;
        opacity: 0.9;
    }
    
    /* Inline Metric & Score Pills */
    .pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        line-height: 1.4;
        margin-right: 5px;
    }
    .pill-score { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .pill-sem   { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .pill-lex   { background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }
    .pill-pop   { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .badge-lat  { background: #dcfce7; color: #166534; font-weight: 700; padding: 2px 6px; border-radius: 6px; }
    .badge-lat-warn { background: #ffedd5; color: #9a3412; font-weight: 700; padding: 2px 6px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


# Pre-warm search engine singleton
@st.cache_resource(show_spinner=False)
def load_engine():
    return HybridSearchEngine.get_instance(DB_URL)


def run_baseline_search(query: str, limit: int = 5):
    """Executes the naive SQL ILIKE baseline query with timing."""
    t0 = time.time()
    words = query.strip().split()
    if not words:
        return [], 0.0
    conditions = []
    params = {}
    for idx, w in enumerate(words):
        pname = f"w_{idx}"
        params[pname] = f"%{w}%"
        conditions.append(f"""
            (p.name_en ILIKE %({pname})s OR 
             p.name_ar ILIKE %({pname})s OR 
             p.brand_en ILIKE %({pname})s OR 
             p.brand_ar ILIKE %({pname})s)
        """)
    sql = f"""
        SELECT 
            p.id, p.sku, p.name_en, p.name_ar, p.brand_en, p.brand_ar,
            c.name_en AS category_en, s.name_en AS subcategory_en,
            p.price, p.size_en, p.unit, p.popularity_score
        FROM products p
        JOIN subcategories s ON p.subcategory_id = s.id
        JOIN categories c ON s.category_id = c.id
        WHERE p.is_active = true
          AND ({" OR ".join(conditions)})
        ORDER BY p.popularity_score DESC
        LIMIT {limit};
    """
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [desc[0] for desc in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        dt = (time.time() - t0) * 1000.0
        return rows, dt
    except Exception:
        return [], 0.0


# ---------------------------------------------------------------------------
# 1. Compact Header & Collapsible Benchmark Summary Strip
# ---------------------------------------------------------------------------
st.markdown('<div class="main-title">🛒 Egyptian Grocery Search — Baseline SQL vs. Hybrid AI Search</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Live executive evaluation of multilingual semantic search, pg_trgm fuzzy matching, Franco-Arabic expansion, and popularity ranking.</div>', unsafe_allow_html=True)

with st.expander("📊 View 100-Query Benchmark Summary", expanded=False):
    m_col1, m_col2 = st.columns([1.2, 1])
    with m_col1:
        st.markdown("**Core Performance Metrics (100 Golden Queries Evaluation):**")
        st.markdown("""
| Metric | ❌ Baseline SQL ILIKE | ✅ Hybrid Smart Search (Ours) | Relative Delta |
| :--- | :--- | :--- | :--- |
| **Recall@5** | 33.0% (33/100) | **86.0% (86/100)** | **+160.6% (+53 queries)** |
| **MRR@5** | 0.3200 | **0.8067** | **+152.1% (+0.4867)** |
| **Zero-Results Rate** | 67.0% (67 dead ends) | **0.0% (0 dead ends)** | **-100.0% elimination** |
| **p95 Latency** | 2.15 ms | **132.11 ms** | **Sub-150ms budget preserved** |
""")
    with m_col2:
        st.markdown("**Recall@5 by Egyptian Query Archetype:**")
        st.markdown("""
| Query Bucket | Baseline ILIKE | Hybrid AI Search | Impact |
| :--- | :--- | :--- | :--- |
| **Standard Arabic** | 84.0% | **96.0%** | +14.3% boost |
| **Franco & Typos** | 20.0% | **84.0%** | **+320.0% boost** |
| **Local Slang & Dialect** | 16.0% | **84.0%** | **+425.0% boost** |
| **Intent & Recipes** | 12.0% | **80.0%** | **+566.7% boost** |
""")

# Load search engine
engine = load_engine()

# Manage state for search query
if "search_query" not in st.session_state:
    st.session_state["search_query"] = "gehina laban"

# ---------------------------------------------------------------------------
# 2. Interactive Control Bar (Top of Page)
# ---------------------------------------------------------------------------
search_input = st.text_input(
    "Search Grocery Catalog",
    value=st.session_state["search_query"],
    placeholder="Try searching in Arabic, English, Franco, or by meal intent (e.g. gehina laban, قوطة, سحور رمضان)...",
    label_visibility="collapsed"
)

# Row 2: Quick Test Presets
st.markdown("<div style='font-size: 12px; font-weight: 600; color: #475569; margin-top: 4px; margin-bottom: 6px;'>⚡ Quick Test Presets (Click to Execute):</div>", unsafe_allow_html=True)
p1, p2, p3, p4, p5, p6 = st.columns(6)

with p1:
    if st.button("🔤 Franco: \"gehina laban\"", use_container_width=True):
        st.session_state["search_query"] = "gehina laban"
        st.rerun()

with p2:
    if st.button("🔤 Franco: \"makrona\"", use_container_width=True):
        st.session_state["search_query"] = "makrona"
        st.rerun()

with p3:
    if st.button("🗣️ Slang: \"شيبسي كباب\"", use_container_width=True):
        st.session_state["search_query"] = "شيبسي كباب"
        st.rerun()

with p4:
    if st.button("🗣️ Slang: \"قوطة\"", use_container_width=True):
        st.session_state["search_query"] = "قوطة"
        st.rerun()

with p5:
    if st.button("🌙 Intent: \"سحور رمضان\"", use_container_width=True):
        st.session_state["search_query"] = "سحور رمضان"
        st.rerun()

with p6:
    if st.button("🎂 Intent: \"مقادير صينية كيكة\"", use_container_width=True):
        st.session_state["search_query"] = "مقادير صينية كيكة"
        st.rerun()

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3. Side-by-Side Comparison View (2 Equal Columns)
# ---------------------------------------------------------------------------
query_text = search_input.strip()

if query_text:
    # 1. Execute Baseline
    base_items, base_latency = run_baseline_search(query_text, limit=5)
    
    # 2. Execute Hybrid Smart Search
    t0_hyb = time.time()
    hyb_items = engine.search_products(query_text, limit=5)
    hyb_latency = (time.time() - t0_hyb) * 1000.0

    col_baseline, col_hybrid = st.columns(2, gap="large")

    # =======================================================================
    # LEFT COLUMN: ❌ Baseline: SQL ILIKE
    # =======================================================================
    with col_baseline:
        hit_color = "#dc2626" if len(base_items) == 0 else "#2563eb"
        st.markdown(f"""
        <div class="status-banner banner-baseline">
            <span style="font-weight: 700; font-size: 14px;">❌ Baseline: SQL ILIKE</span>
            <span>
                Hits: <strong style="color: {hit_color};">{len(base_items)}</strong> &nbsp;|&nbsp; 
                Latency: <strong style="color: #475569;">{base_latency:.1f} ms</strong>
            </span>
        </div>
        """, unsafe_allow_html=True)

        if not base_items:
            st.markdown("""
            <div class="dead-end-card">
                <div class="dead-end-title">0 Products Found — Customer hits a dead end.</div>
                <div class="dead-end-desc">
                    SQL ILIKE failed due to lack of dialect stemming, typo tolerance, or Franco transliteration.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for rank, prod in enumerate(base_items, 1):
                with st.container(border=True):
                    # Row 1: Rank, Arabic Name (RTL Cairo), Price
                    c_rank, c_name, c_price = st.columns([1, 7, 2])
                    with c_rank:
                        st.markdown(f"<span style='font-size: 14px; font-weight: 700; color: #475569;'>#{rank}</span>", unsafe_allow_html=True)
                    with c_name:
                        st.markdown(f'<div class="ar-title">{prod.get("name_ar")}</div>', unsafe_allow_html=True)
                    with c_price:
                        price_str = f"{prod['price']:.2f} EGP" if prod.get('price') else "N/A"
                        st.markdown(f"<div style='text-align: right; font-weight: 700; color: #0f172a; font-size: 14px;'>{price_str}</div>", unsafe_allow_html=True)
                    
                    # Row 2: English Name, Brand, Size, Category
                    b_brand = f" • Brand: {prod['brand_en']}" if prod.get('brand_en') else ""
                    b_size = f" • {prod.get('size_en', '')}" if prod.get('size_en') else ""
                    st.caption(f"{prod.get('name_en')}{b_brand}{b_size} | {prod.get('category_en')} > {prod.get('subcategory_en')}")

    # =======================================================================
    # RIGHT COLUMN: ✅ Hybrid Smart Search: pgvector + pg_trgm + LTR
    # =======================================================================
    with col_hybrid:
        lat_pill_class = "badge-lat" if hyb_latency < 150 else "badge-lat-warn"
        st.markdown(f"""
        <div class="status-banner banner-hybrid">
            <span style="font-weight: 700; font-size: 14px;">✅ Hybrid Smart Search: pgvector + pg_trgm + LTR</span>
            <span>
                Hits: <strong style="color: #166534;">{len(hyb_items)}</strong> &nbsp;|&nbsp; 
                Latency: <span class="{lat_pill_class}">{hyb_latency:.1f} ms</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        if not hyb_items:
            st.warning("No products matched the hybrid search query.")
        else:
            for rank, prod in enumerate(hyb_items, 1):
                with st.container(border=True):
                    # Row 1: Rank, Arabic Name (RTL Cairo), Price
                    c_rank, c_name, c_price = st.columns([1, 7, 2])
                    with c_rank:
                        st.markdown(f"<span style='font-size: 14px; font-weight: 700; color: #166534;'>#{rank}</span>", unsafe_allow_html=True)
                    with c_name:
                        st.markdown(f'<div class="ar-title">{prod.get("name_ar")}</div>', unsafe_allow_html=True)
                    with c_price:
                        price_str = f"{prod['price']:.2f} EGP" if prod.get('price') else "N/A"
                        st.markdown(f"<div style='text-align: right; font-weight: 700; color: #166534; font-size: 14px;'>{price_str}</div>", unsafe_allow_html=True)
                    
                    # Row 2: English Name, Brand, Size, Category
                    h_brand = f" • Brand: {prod['brand_en']}" if prod.get('brand_en') else ""
                    h_size = f" • {prod.get('size_en', '')}" if prod.get('size_en') else ""
                    st.caption(f"{prod.get('name_en')}{h_brand}{h_size} | {prod.get('category_en')} > {prod.get('subcategory_en')}")
                    
                    # Row 3: Score Breakdown Pills
                    st.markdown(f"""
                    <div style="margin-top: 3px; display: flex; flex-wrap: wrap; gap: 4px;">
                        <span class="pill pill-score">Score: {prod.get('final_score', 0):.2f}</span>
                        <span class="pill pill-sem">🧠 Sem: {prod.get('semantic_score', 0):.2f}</span>
                        <span class="pill pill-lex">🔤 Lex: {prod.get('lexical_score', 0):.2f}</span>
                        <span class="pill pill-pop">🔥 Pop: {prod.get('popularity_score', 0):.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)
