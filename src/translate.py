# -*- coding: utf-8 -*-
"""Сборка русской карточки. Приоритет: сохранённые в БД (обогащённые) поля > разбор заголовка.
Никогда не выдаёт фразу «не распознано/не определено» — неизвестное поле просто пустое."""
import re
from hebrew import parse

SOURCES_RU = {
    "Gov.il": "Минздрав Израиля (Gov.il)",
    "YNET": "Ynet (новости)",
    "Ynet": "Ynet (новости)",
    "Ynet Health": "Ynet (здоровье)",
    "Ynet Search": "Ynet (новости)",
    "מעריב": "Маарив (новости)",
    "ישראל היום": "Исраэль ха-йом (новости)",
    "ice": "ICE (новости)",
    "haipo.co.il": "Haipo (предупреждения о кошерности)",
    "nws.report": "NWS Report (иврит)",
    "emess.co.il": "emess.co.il",
}
def src_ru(s: str) -> str:
    return SOURCES_RU.get(s, s)

FOODS = [
    (r"גליד\S*", "мороженое"), (r"טחינ\S*", "тхина (кунжутная паста)"),
    (r"שזיפים מיובשים", "чернослив"), (r"דאודורנט\S*", "дезодорант"),
    (r"עוגי\S*", "печенье"), (r"קמח", "мука"), (r"גבינ\S*", "сыр"),
    (r"שוקולד", "шоколад"), (r"חטיף\S*", "снек"), (r"מעדן\S*", "десерт"),
    (r"תירס", "кукуруза"), (r"בייק רול", "бейк-ролл"), (r"לחם", "хлеб"),
    (r"סלמון", "лосось"), (r"גזר", "морковь"), (r"חסה", "салат-латук"),
    (r"ביצים", "яйца"), (r"שמן", "масло"), (r"מיץ", "сок"),
    (r"צעצוע\S*", "игрушки"), (r"בייבי שארק", "Baby Shark"),
    (r"תמ\"ל|נוטרילון", "детская смесь"),
]

def _clean_product(q: list) -> list:
    out = []
    for s in q:
        s = re.sub(r"^(ריקול|הודעה על החזרה יזומה|קריאה להחזרה)\s*/?\s*", "", s).strip()
        s = re.sub(r"^(של|של\S*)\s+", "", s).strip()
        ru = s
        for pat, r in FOODS:
            if re.search(pat, s):
                ru = r if len(s) <= 25 else r
                break
        out.append(ru)
    return out

GENERIC_REASON = "смотрите оригинал объявления (типовая причина не распознана)"

def build_card(item: dict) -> dict:
    p = parse(item["he_title"], item["source"])
    _HE = ("ynet", "walla", "israelhayom", "kipa", "gov.il", "maariv", "ice.co.il", "emess")
    orig_lang = "иврит" if any(s in (item.get("url", "") + item.get("source", "")).lower() for s in _HE) else "русский"

    # --- базовый разбор заголовка ---
    reason = p.get("reason_ru") or item.get("reason_ru") or ""
    guessed = reason != ""
    product = " / ".join(_clean_product(p["quoted"][:3])) if p["quoted"] else item.get("product") or ""
    product = " ".join(w for w in product.split() if not re.search(r"[\u05d0-\u05ea]", w)).strip()
    product = re.sub(r"\s*/\s*$|^\s*/\s*", "", product).strip(" /")
    brands = item.get("brands") if item.get("brands") not in (None, "", "—") else (", ".join(p["brands"]) if p["brands"] else "")
    category = item.get("category_ru") if item.get("category_ru") not in (None, "", "не определена") else p.get("category_ru")
    baby = bool(item.get("baby")) or bool(p.get("baby"))
    title = item.get("title_ru") or ""
    if "смотрите оригинал" in title or "Отзыв" in title:
        title = ""
    if not title:
        if product:
            title = f"Изъятие: {product} — {reason}" if reason else f"Изъятие: {product}"
        else:
            title = f"Изъятие продукта — {reason}" if reason else "Изъятие продукта в Израиле"
    # скрыть служебную фразу-заглушку
    if GENERIC_REASON in reason:
        reason = ""
    from datetime import datetime
    pub = datetime.fromisoformat(item["published"]).strftime("%d.%m.%Y")
    return {
        **item,
        "title_ru": title,
        "reason_ru": reason,
        "category_ru": category or "не определена",
        "baby": baby,
        "brands": brands or "—",
        "product": product or "—",
        "guessed": guessed,
        "official": p["official"],
        "source_ru": src_ru(item["source"]),
        "orig_lang": orig_lang,
        "pub_short": pub,
    }
