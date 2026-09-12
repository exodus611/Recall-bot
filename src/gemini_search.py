# -*- coding: utf-8 -*-
"""Поиск прямой URL статьи через Gemini (grounding with Google Search).
Только стандартная библиотека (urllib) — requirements не расширяяем!
Нужен GEMINI_API_KEY в секретах. Без ключа/при ошибке — тихо [], бот работает штатно.
ВАЖНО: берём URL только из реальных результатов поиска (groundingChunks)."""
import os, re, json, urllib.request, urllib.parse

NEWS_OK = re.compile(r"(ynet|walla|israelhayom|מעריב|maariv|ice\.co\.il|kipa|nws\.report|gov\.il|news\.co\.il|13tv|now14|kan|1news|mako|calcalist|globes|jdn|srugy|bhol|0404|israelnationalnews|lada\.net|cursorinfo|vesty)", re.I)
BAD = re.compile(r"(google\.|youtube|facebook|twitter|x\.com|t\.me|instagram|tiktok|wikipedia)", re.I)
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]

def _key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")

def search_urls(query: str, timeout: int = 45) -> list:
    """Реальные URL из результатов Google-поиска (grounding). [] если ключа нет/ошибка."""
    key = _key()
    if not key:
        return []
    body = json.dumps({
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],
    }).encode("utf-8")
    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={urllib.parse.quote(key)}"
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cand = (data.get("candidates") or [{}])[0]
            chunks = cand.get("groundingMetadata", {}).get("groundingChunks", []) or []
            urls = []
            for ch in chunks:
                u = (ch.get("web") or {}).get("uri") or ""
                if u and u not in urls:
                    urls.append(u)
            if urls:
                return urls
        except Exception:
            continue
    return []

def resolve_article(he_title: str) -> str:
    """Прямой URL новости по иврит-заголовку. Пустая строка, если не нашли."""
    if not he_title:
        return ""
    urls = search_urls(f"ריקול החזרה יזומה {he_title}")
    good = [u for u in urls if NEWS_OK.search(u) and not BAD.search(u)]
    if good:
        return good[0]
    neutral = [u for u in urls if not BAD.search(u)]
    return neutral[0] if neutral else ""
