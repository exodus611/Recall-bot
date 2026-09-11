# -*- coding: utf-8 -*-
"""Обогащение карточки из статьи с ПРЯМОЙ ссылкой (официальные RSS СМИ, напр. Ynet):
og:image (фото продукта) + номера партий/сроки из текста. Один вежливый GET, таймауты,
любая ошибка -> карточка остаётся текстовой. Никакого обхода защит: страница либо
отдаётся обычному клиенту, либо мы отступаем."""
import re, html, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) recall-bot/1.0"}

def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def enrich(direct_url: str) -> dict:
    out = {"photo_url": None, "batches": [], "dates": [], "barcodes": [],
           "maker": None, "found_batches": False}
    if not direct_url or "news.google.com" in direct_url:
        return out
    try:
        h = _get(direct_url)
    except Exception:
        return out
    m = re.search(r'property=["\']og:image["\'] content=["\']([^"\']+)["\']', h)
    if m: out["photo_url"] = m.group(1)
    text = html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", h, flags=re.S))
    text = re.sub(r"\s+", " ", text)
    # номера партий: BATCH/LOT/דגם + код
    for m in re.finditer(r"(?:BATCH(?:\s+NO\.?)?|LOT|מספר דגם|דגם)\s*[:\-]?\s*([A-Za-z0-9]+(?:\s?[A-Za-z0-9]{2,8})?)", text):
        code = m.group(1).strip(" .,;-")
        if 2 <= len(code) <= 20 and re.search(r"\d", code) and code not in out["batches"]:
            out["batches"].append(code)
    # даты
    out["dates"] = sorted(set(re.findall(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b", text)))[:8]
    # штрих-коды (баркоды) — факт, копирайта нет
    out["barcodes"] = sorted(set(re.findall(r"(?:ברקוד(?:\s+מוצר)?|barcode)\s*:?\s*(\d{8,14})", text)))[:8]
    m = re.search(r"(?:יצרן|יבואן|מיובא(?:ת)? על(?:\s+ידי)?)\s*:?\s*([A-Za-z\u05d0-\u05ea][^.,;]{2,45})", text)
    if m: out["maker"] = m.group(1).strip()
    out["found_batches"] = bool(out["batches"] or out["dates"] or out["barcodes"])
    return out
