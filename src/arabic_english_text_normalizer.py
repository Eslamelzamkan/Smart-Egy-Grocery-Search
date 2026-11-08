import re
import os
import sys
import unicodedata
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# Regex for Tashkeel (Arabic diacritical marks) and Tatweel
RE_TASHKEEL = re.compile(r'[\u064B-\u065F\u0670]')
RE_TATWEEL = re.compile(r'\u0640')
RE_ALEF = re.compile(r'[أإآٱ]')
RE_HAMZA_WAW = re.compile(r'ؤ')
RE_HAMZA_YEH = re.compile(r'ئ')
RE_TEH_MARBUTA = re.compile(r'ة')
RE_ALEF_MAKSURA = re.compile(r'ى')
RE_WHITESPACE = re.compile(r'\s+')
RE_PUNCTUATION = re.compile(r'[^\w\s\u0600-\u06FF]')


# ---------------------------------------------------------------------------
# 1. Subcategory Intent & Usage Occasion Tags Dictionary
# ---------------------------------------------------------------------------
SUBCATEGORY_INTENT_TAGS = {
    # Breakfast & Ramadan Suhoor staples
    "Cheese": "فطار عشاء سحور رمضان سندوتشات المدرسة للأطفال جبنة بيضا رومي فيتا شيدر فطار مصري خفيف وسريع breakfast dinner suhoor sandwiches",
    "Yogurt": "فطار عشاء سحور رمضان زبادي خفيف هضم رايب دايت breakfast suhoor digest light rayeb yogurt",
    "Milk": "فطار سحور شاي باللبن حليب كامل خالي الدسم دايت كيك breakfast suhoor baking tea milk",
    "Canned Food": "فول مدمس تونة سحور رمضان فطار وجبة سريعة معلبات fava beans tuna suhoor quick meal breakfast",
    "Breakfast Cereals": "فطار خفيف سريع أطفال كورن فليكس حبوب إفطار breakfast cereals kids light morning",
    "Jam & Honey": "فطار سندوتشات عسل نحل طبيعي لتقوية المناعة مربى طاقة حلويات breakfast sandwiches pure honey energy immunity",
    "Bakery": "عيش بلدي توست مخبوزات سندوتشات المدرسة فطار سحور برجر فينو كرواسون bread toast sandwiches bakery breakfast",

    # Baking, Cake Ingredients & Desserts
    "Sugar & Flour": "حلويات مقادير صينية كيكة منزلية خبيز معجنات دقيق فاخر سكر ناعم للحلويات نشا بيكنج بودر baking cake ingredients desserts pastry",
    "Biscuits & Cakes": "حلويات شاي بسكويت كيك تحلية سريعة بعد الغداء سناكس شوكولاتة مولتو desserts biscuits tea cake snacks",
    "Snacks & Sweets": "شوكولاتة حلويات تحلية سريعة بعد الغداء كاندي سناك chocolate sweets desserts snacks candy",
    "Dates": "رمضان ياميش إفطار تمر تمور بلح صيام ramadan dates fasting breakfast",
    "Nuts & Dried Fruit": "ياميش رمضان مكسرات وياميش للتسلية تسالي سهرة ماتش كاجو لوز بندق فستق nuts dried fruits ramadan match night",

    # Cooking, Dinner, Lunch & Meal Preparation
    "Rice & Pasta": "غداء طبخ مكونات حلة مكرونة بالصلصة حمراء أرز مصري كسر خفيف بسمتي لسان عصفور قلم للفرن dinner lunch pasta spaghetti rice cooking",
    "Oil & Ghee": "طبخ تحمير سمنة بلدي بقري نباتي زيت ذرة عباد شمس خليط زيتون قلي cooking frying ghee oil",
    "Spices": "بهارات تتبيل وطبخ صينية فراخ مشوية لحمة طاجن توابل دجاج مشوي مرقة فلفل اسود كمون كزبرة بابريكا spices seasoning chicken meat stew",
    "Sauces": "صلصة طماطم تسبيكة كاتشب مايونيز خل أبيض نقي طحينة صوص sauce tomato paste ketchup vinegar tahini cooking",
    "Vegetables": "خضار طازج لطبق السلطة الخضراء بصل طماطم خيار بطاطس فلفل باذنجان بامية cooking fresh vegetables green salad",
    "Fruits": "فواكه طازجة غنية بالفيتامينات فيتامين سي برتقال بلدي تفاح موز fresh fruits vitamins healthy",
    "Frozen Vegetables": "خضار مجمد مكونات طاجن بامية بالصلصة بسلة خضار مشكل ملوخية بطاطس بوم فريت نصف مقلية frozen vegetables okra peas stew",
    "Poultry": "فراخ دجاج بانيه غداء شوي صينية دواجن poultry chicken dinner cooking roast",
    "Frozen": "وجبة سريعة التحضير ناجتس وبرجر بطاطس بوم فريت نصف مقلية frozen quick meal burger fries nuggets",
    "Beef & Lamb": "لحمة بلدي مفروم كباب حلة شوي برجر كفتة غداء beef lamb meat burger cooking",

    # Household Cleaning & Disinfection
    "Household Cleaners": "تنظيف الحمام والمطبخ والتعقيم والمنزل تطهير كلور ديتول bathroom kitchen cleaning disinfect",
    "Dishwashing": "غسيل الصحون وإزالة دهون الحلل صابون مواعين بريل فيري ليمون أطباق dishwashing liquid grease plates",
    "Laundry": "غسيل الملابس البيضاء والناصعة مسحوق غسيل اوتوماتيك يدوي جل معطر ملابس اريال برسيل تايد laundry detergent powder",
    "Cleaning & Paper": "مناديل ورقية للمطبخ والسفرة تواليت رول بكر امتصاص عالي جيب زينة فلورا فاين paper tissues kitchen bathroom towels",
    "Soap & Shower": "مستلزمات شاور واستحمام يومي نظافة صابون سائل غسول يدين شامبو شاور جل لايف بوي دوف لوكس ديتول shower bath soap shampoo hygiene",
    "Personal Care": "عناية شخصية نظافة معجون أسنان حلاقة وفرشاة مزيل عرق personal care hygiene oral shaving",

    # Beverages & Drinks
    "Tea & Herbs": "شاي أعشاب مشروب سخن للشتاء والدفا يانسون نعناع كركديه أخضر فتلة ناعم ليبتون العروسة hot winter drink tea herbs warm cozy",
    "Coffee": "قهوة صباحية لتعديل المزاج تركي محوج بالحبهان نسكافيه بلاك سادة كابتشينو كافيين تركيز morning coffee espresso caffeine focus",
    "Juices": "عصائر طبيعية مثلجة للضيوف انتعاش الصيف مانجو جوافة برتقال فيتامينات جهينة بيتي لمار fresh cold juices summer guest refreshment",
    "Soft Drinks": "مشروبات غازية كانز ساقع كوكاكولا بيبسي سفن اب دايت انتعاش صودا soft drinks cans soda cold",
    "Energy Drinks": "مشروبات طاقة وانتعاش للجيم تمرين باور هورس ريد بول مونستر energy drinks gym workout",
    "Water": "مياه شرب معدنية طبيعية ترطيب صحة زجاجة نستله بركة حياة mineral drinking water hydration healthy",

    # Baby Care
    "Baby": "أكل أطفال صحي ومغذي حفاضات بيبي بامبرز سيريلاك قمح فواكه لبن أطفال baby food nutrition diapers cerelac",
    "Baby Food": "أكل أطفال صحي ومغذي سيريلاك قمح باللبن فواكه أرز وجبات رضع baby food nutrition cerelac infant",
    "Diapers": "حفاضات أطفال عناية بيبي غيار بامبرز مولفيكس بيبي جوي baby diapers infant care",

    # Snacks & Entertainment
    "Chips & Crisps": "شيبسي مقرمشات سناك مقرمش للتسالي وسهرة الماتش بطاطس كباب جبنة طماطم ملح كاتشب ليز chips crisps snacks movie match entertainment"
}


# ---------------------------------------------------------------------------
# 2. Franco-to-Arabic Phonetic Transliteration Dictionary
# ---------------------------------------------------------------------------
FRANCO_GROCERY_MAP = {
    # Brands
    "gehina": "جهينة",
    "gohayna": "جهينة",
    "juhayna": "جهينة",
    "johayna": "جهينة",
    "shepsy": "شيبسي",
    "chipsy": "شيبسي",
    "shibsi": "شيبسي",
    "dolex": "ديتول",
    "detol": "ديتول",
    "dettol": "ديتول",
    "beril": "بريل",
    "pril": "بريل",
    "fairy": "فيري",
    "ariel": "اريال",
    "persil": "برسيل",
    "nescafe": "نسكافيه",
    "cadbury": "كادبوري",
    "galaxy": "جالاكسي",
    "lamar": "لمار",
    "almarai": "المراعي",
    "marai": "المراعي",
    "lactel": "لاكتيل",
    "danone": "دانون",
    "domty": "دومتي",
    "crystal": "كريستال",
    "heinz": "هاينز",

    # Grocery Categories & Ingredients
    "makrona": "مكرونة",
    "macrona": "مكرونة",
    "spageti": "سباجيتي",
    "spaghetti": "سباجيتي",
    "gibna": "جبنة",
    "gebna": "جبنة",
    "gebneh": "جبنة",
    "rumi": "رومي",
    "roumi": "رومي",
    "roumy": "رومي",
    "laban": "لبن",
    "7alib": "حليب",
    "halib": "حليب",
    "rayeb": "رايب",
    "foul": "فول",
    "ful": "فول",
    "medames": "مدمس",
    "zeit": "زيت",
    "zayt": "زيت",
    "dorah": "ذرة",
    "dora": "ذرة",
    "3abad": "عباد",
    "shams": "شمس",
    "samna": "سمنة",
    "samnah": "سمنة",
    "baladi": "بلدي",
    "3esh": "عيش",
    "eish": "عيش",
    "aysh": "عيش",
    "zebda": "زبدة",
    "zibda": "زبدة",
    "halawa": "حلاوة",
    "teheya": "طحينة",
    "tahina": "طحينة",
    "choclate": "شوكولاتة",
    "chocolate": "شوكولاتة",
    "shoklata": "شوكولاتة",
    "menadeel": "مناديل",
    "manadeel": "مناديل",
    "mandil": "منديل",
    "shaye": "شاي",
    "shay": "شاي",
    "shai": "شاي",
    "aroosa": "العروسة",
    "3roosa": "العروسة",
    "tamatem": "طماطم",
    "btates": "بطاطس",
    "batates": "بطاطس",
    "potatoes": "بطاطس",
    "basal": "بصل",
    "khiar": "خيار",
    "tofa7": "تفاح",
    "toffah": "تفاح",
    "burtuqal": "برتقال",
    "bortoqal": "برتقال",
    "sabon": "صابون",
    "saboon": "صابون",
    "mwa3een": "مواعين",
    "skkar": "سكر",
    "sokar": "سكر",
    "sugar": "سكر",
    "daqeeq": "دقيق",
    "daeeq": "دقيق",
    "flour": "دقيق",
    "moraba": "مربى",
    "3asal": "عسل",
    "asal": "عسل",
    "honey": "عسل",
    "basterma": "بسطرمة",
    "tonah": "تونة",
    "tona": "تونة",
    "khall": "خل",
    "khal": "خل",
    "zaytoon": "زيتون",
    "zeytoun": "زيتون",
    "olives": "زيتون",
    "bamyah": "بامية",
    "bamia": "بامية",
    "karkadeh": "كركديه",
    "7alawa": "حلاوة",
    "mya": "مياه",
    "mayya": "مياه"
}

# Standard English terms that already exist in English product/brand names
ENGLISH_CATALOG_TERMS = {
    "juhayna", "chipsy", "dettol", "pril", "fairy", "ariel", "persil",
    "nescafe", "cadbury", "galaxy", "lamar", "almarai", "lactel",
    "danone", "domty", "crystal", "heinz", "spaghetti", "chocolate",
    "potatoes", "sugar", "flour", "honey", "olives", "halawa"
}


def transliterate_franco_words(text: str) -> list[str]:
    """
    Extracts phonetic Arabic equivalents for any Franco grocery terms in the query.
    """
    if not text:
        return []
    words = RE_PUNCTUATION.sub(' ', text.lower()).split()
    matched_arabic = []
    for w in words:
        if w in FRANCO_GROCERY_MAP:
            matched_arabic.append(FRANCO_GROCERY_MAP[w])
    return matched_arabic


def normalize_text(text: str | None) -> str:
    """
    Normalizes Egyptian Arabic, Franco-Arab, and English text with uniform rules:
    - Unifies Arabic Alef/Hamza variants before stripping Latin accents
    - Strips European accents (é -> e, etc.)
    - Strips Tashkeel and Tatweel
    - Unifies Teh Marbuta (ة -> ه) and Alef Maksura (ى -> ي)
    - Lowercases English / Franco text and collapses whitespace
    """
    if not text:
        return ""
    
    # 1. Unify Arabic Alef & Hamza forms before NFKD decomposition
    s = RE_ALEF.sub('ا', text)
    s = RE_HAMZA_WAW.sub('و', s)
    s = RE_HAMZA_YEH.sub('ي', s)
    
    # 2. Unicode NFKD normalization to strip European accents
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    
    # 3. Strip explicit Tashkeel & Tatweel
    s = RE_TASHKEEL.sub('', s)
    s = RE_TATWEEL.sub('', s)
    
    # 4. Unify Teh Marbuta and Alef Maksura
    s = RE_TEH_MARBUTA.sub('ه', s)
    s = RE_ALEF_MAKSURA.sub('ي', s)
    
    # 5. Lowercase and collapse extra whitespace
    s = s.lower()
    s = RE_WHITESPACE.sub(' ', s).strip()
    return s


# Egyptian Arabic Slang / Dialect Synonym Mapping
EGYPTIAN_SLANG_MAP = {
    "قوطة": "طماطم",
    "قوطه": "طماطم",
    "اوطة": "طماطم",
    "اوطه": "طماطم",
    "شيبسى": "شيبسي",
    "شيبسي": "شيبسي",
}


def normalize_and_expand_query(query: str | None) -> str:
    """
    Normalizes incoming query:
    1. Replaces Egyptian slang and pure Franco/typo words directly with canonical Arabic
       so trigram word_similarity is not diluted by non-existent Latin spellings.
    2. Retains valid English catalog terms while appending their Arabic equivalents.
    """
    if not query:
        return ""
    clean = normalize_text(query)
    words = clean.split()
    
    out_words = []
    appended_arabic = []
    
    for w in words:
        w_key = RE_PUNCTUATION.sub('', w)
        if w_key in EGYPTIAN_SLANG_MAP:
            out_words.append(normalize_text(EGYPTIAN_SLANG_MAP[w_key]))
        elif w_key in FRANCO_GROCERY_MAP:
            ar_word = normalize_text(FRANCO_GROCERY_MAP[w_key])
            if w_key in ENGLISH_CATALOG_TERMS:
                out_words.append(w)
                appended_arabic.append(ar_word)
            else:
                out_words.append(ar_word)
        else:
            out_words.append(w)
            
    combined = " ".join(out_words + appended_arabic)
    return normalize_text(combined)


def build_rich_search_text(
    name_en: str | None,
    name_ar: str | None,
    brand_en: str | None,
    brand_ar: str | None,
    category_en: str | None,
    category_ar: str | None,
    subcategory_en: str | None,
    subcategory_ar: str | None,
    size_en: str | None,
    size_ar: str | None,
    unit: str | None
) -> str:
    """
    Constructs the canonical rich search string:
    [name_en] | [name_ar] | Brand: [brand_en] [brand_ar] | Category: [category_en] [category_ar] > [subcategory_en] [subcategory_ar] | Usage: [intent_tags] | Size: [size_en] [size_ar] [unit]
    and normalizes the final combined text.
    """
    parts = []
    
    # Names
    name_part = f"{name_en or ''} | {name_ar or ''}".strip(" |")
    if name_part:
        parts.append(name_part)
        
    # Brand
    brand_val = f"{brand_en or ''} {brand_ar or ''}".strip()
    if brand_val:
        parts.append(f"Brand: {brand_val}")
        
    # Hierarchy
    cat_val = f"{category_en or ''} {category_ar or ''}".strip()
    subcat_val = f"{subcategory_en or ''} {subcategory_ar or ''}".strip()
    if cat_val or subcat_val:
        parts.append(f"Category: {cat_val} > {subcat_val}".strip(" >"))
        
    # Intent / Usage Occasion Tags
    if subcategory_en and subcategory_en in SUBCATEGORY_INTENT_TAGS:
        intent_tags = SUBCATEGORY_INTENT_TAGS[subcategory_en]
        parts.append(f"Usage: {intent_tags}")
        
    # Size / Unit
    size_val = f"{size_en or ''} {size_ar or ''} {unit or ''}".strip()
    if size_val:
        parts.append(f"Size: {size_val}")
        
    raw_rich_text = " | ".join(parts)
    return normalize_text(raw_rich_text)


def populate_products_search_text(db_url: str | None = None) -> int:
    """
    Fetches all products joined with subcategories and categories,
    computes enriched search_text with usage tags, and updates products.search_text.
    """
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/product_ai_training")
        
    query_fetch = """
        SELECT 
            p.id,
            p.name_en,
            p.name_ar,
            p.brand_en,
            p.brand_ar,
            c.name_en AS category_en,
            c.name_ar AS category_ar,
            s.name_en AS subcategory_en,
            s.name_ar AS subcategory_ar,
            p.size_en,
            p.size_ar,
            p.unit
        FROM products p
        JOIN subcategories s ON p.subcategory_id = s.id
        JOIN categories c ON s.category_id = c.id;
    """
    
    query_update = """
        UPDATE products 
        SET search_text = %(search_text)s 
        WHERE id = %(id)s;
    """
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query_fetch)
            rows = cur.fetchall()
            
            update_data = []
            for r in rows:
                p_id, n_en, n_ar, b_en, b_ar, c_en, c_ar, s_en, s_ar, sz_en, sz_ar, unit = r
                rich_text = build_rich_search_text(
                    n_en, n_ar, b_en, b_ar, c_en, c_ar, s_en, s_ar, sz_en, sz_ar, unit
                )
                update_data.append({"id": p_id, "search_text": rich_text})
                
            cur.executemany(query_update, update_data)
            conn.commit()
            print(f"Successfully populated enriched search_text for {len(update_data)} products.")
            return len(update_data)


if __name__ == "__main__":
    populate_products_search_text()