# -*- coding: utf-8 -*-
"""Сборка русской карточки из ивритского заголовка (словарь, без ИИ)."""
import re
from hebrew import parse

SOURCES_RU = {
    "Gov.il": "Минздрав Израиля (Gov.il)",
    "YNET": "Ynet (новости)",
    "מעריב": "Маарив (новости)",
    "ישראל היום": "Исраэль ха-йом (новости)",
    "ice": "ICE (новости)",
    "haipo.co.il": "Haipo (предупреждения о кошерности)",
    "Ynet Search": "Ynet (новости)",
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
]

def clean_product(q: list[str]) -> list[str]:
    out = []
    for s in q:
        s = re.sub(r"^(ריקול|הודעה על החזרה יזומה|קריאה להחזרה)\s*/?\s*", "", s).strip()
        s = re.sub(r"^(של|של\S*)\s+", "", s).strip()
        if len(s) >= 2 and not re.search(r"[א-ת]{6,}", s.replace(" ", "")) or " " in s:
            # ивритские цепочки переводим по словарюfoods
            ru = s
            for pat, r in FOODS:
                if re.search(pat, s):
                    ru = r + (" " + s if len(s) <= 25 else "")
                    break
            else:
                ru = s if re.search(r"[A-Za-z0-9]", s) else s
            out.append(ru)
    return out or q


def build_card(item: dict) -> dict:
    p = parse(item["he_title"], item["source"])
    _HE = ("ynet", "walla", "israelhayom", "kipa", "gov.il", "maariv", "ice.co.il", "emess")
    orig_lang = "иврит" if any(s in (item.get("url","") + item.get("source","")).lower() for s in _HE) else "русский"
    reason = p["reason_ru"]
    guessed = reason is not None
    reason = reason or "смотрите оригинал объявления (типовая причина не распознана)"
    product = " / ".join(clean_product(p["quoted"][:3])) if p["quoted"] else "— (в заголовке не назван)"
    # русский продукт: убираем ивритские токены (перевод уже в русской части)
    product = " ".join(w for w in product.split() if not re.search(r"[\u05d0-\u05ea]", w)).strip()
    product = re.sub(r"\s*/\s*$|^\s*/\s*", "", product).strip(" /") or "— (см. бренд)"
    brands = ", ".join(p["brands"]) if p["brands"] else "—"
    from datetime import datetime
    pub = datetime.fromisoformat(item["published"]).strftime("%d.%m.%Y")
    title_ru = f"Отзыв: {product} — {reason}" if product != "— (в заголовке не назван)" else f"Отзыв продукта — {reason}"
    return {
        **item,
        "title_ru": title_ru,
        "reason_ru": reason,
        "category_ru": p["category_ru"],
        "baby": p["baby"],
        "brands": brands,
        "product": product,
        "guessed": guessed,
                "official": p["official"], "source_ru": src_ru(item["source"]), "orig_lang": orig_lang,
        "pub_short": pub,
    }
