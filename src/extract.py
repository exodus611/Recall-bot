# -*- coding: utf-8 -*-
"""Схематичный разбор текста объявления/статьи (иврит): стандартные поля,
которые пресса копирует из официального извещения + словари причин/категорий."""
import re
from hebrew import REASONS, CATEGORIES

NEXT = r"(?=\s*(?:שם המוצר|מותג|שם יצרן|יצרן|יבואן|ברקוד|תאריך|משקל|$|[.;]))"
LABELS = {
    "product": r"שם המוצר\s*:?\s*(.+?)" + NEXT,
    "brand":   r"מותג\s*:?\s*(.+?)" + NEXT,
    "maker":   r"(?:שם יצרן|יצרן|יבואן)\s*:?\s*(.+?)" + NEXT,
    "barcode": r"ברקוד(?:\s+מוצר)?\s*:?\s*(\d{8,14})",
    "exp":     r"תאריך\s+(?:תפוגה|ייצור)\s*:?\s*([0-9]{1,2}[./][0-9]{1,2}[./][0-9]{2,4})",
}

def labeled_fields(text: str) -> dict:
    out = {}
    for key, pat in LABELS.items():
        vals = re.findall(pat, text)
        vals = [v.strip(" *_.-–") for v in vals if v and len(v.strip()) > 1]
        if vals:
            # uniq, порядок сохранения
            seen, uniq = set(), []
            for v in vals:
                if v not in seen: seen.add(v); uniq.append(v)
            out[key] = uniq if key in ("barcode", "exp") else uniq[0][:60]
    return out

def reason_from(text: str):
    for pat, ru in REASONS:
        if re.search(pat, text):
            return ru
    return None

def category_from(text: str):
    for pat, ru, baby in CATEGORIES:
        if re.search(pat, text):
            return ru, baby
    return None, False

def analyze(text: str) -> dict:
    """Полный схематичный разбор. Категория/причина — по окну вокруг слов отзыва,
    чтобы меню и «похожие новости» страницы не сбивали определение."""
    t = re.sub(r"\s+", " ", text)
    f = labeled_fields(t)
    m = re.search(r"(?:ריקול|החזרה יזומה|קריאה להחזרה)", t)
    if m:
        a = max(0, m.start() - 300); b = min(len(t), m.start() + 1800)
        window = t[a:b]
    else:
        window = t
    reason = reason_from(window)
    cat, baby = category_from(t[:200]) or (None, None)
    if cat is None:
        cat, baby = category_from(window)
    if reason: f["reason_ru"] = reason
    if cat:    f["category_ru"], f["baby"] = cat, baby
    for k in ("product", "brand", "maker"):
        if k in f and isinstance(f[k], str):
            v = re.split(r"\s*[|,]\s*(?:למען|בתיאום|בעקבות|$)", f[k])[0]
            v = v.strip(' "“”״')
            f[k] = v[:60] if len(v) > 2 else f[k]
    # убрать markdown-звёздочки из значений
    for k, v in list(f.items()):
        if isinstance(v, str):
            f[k] = v.replace("*", "").strip()
        elif isinstance(v, list):
            f[k] = [x.replace("*", "").strip() for x in v]
    return {k: v for k, v in f.items() if v}
