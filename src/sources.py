# -*- coding: utf-8 -*-
"""Источники новостей об отзывах. Основной: Google News RSS (стабилен, без ключей).
Дополнительный: прямой опрос gov.il (может блокироваться Cloudflare — тогда молча пропускаем)."""
import re, urllib.request, urllib.parse, html
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) recall-bot/1.0"}

RSS = ('https://news.google.com/rss/search?q='
       + urllib.parse.quote('"החזרה יזומה" OR "ריקול מוצר" OR "קריאה להחזרה" when:30d')
       + '&hl=he&gl=IL&ceid=IL:he')

def _get(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _clean(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def fetch_google_news() -> list[dict]:
    """Возвращает свежие публикации об отзывах: {id, he_title, url, source, published}"""
    raw = _get(RSS).decode("utf-8", "ignore")
    items = []
    for block in re.findall(r"<item>(.*?)</item>", raw, re.S):
        title = _clean(re.search(r"<title>(.*?)</title>", block, re.S).group(1))
        link = re.search(r"<link>(.*?)</link>", block, re.S).group(1).strip()
        pub = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        src = re.search(r"<source[^>]*>(.*?)</source>", block, re.S)
        source = _clean(src.group(1)) if src else "press"
        # Отделяем хвост "- Источник" от заголовка
        he_title = re.sub(r"\s*-\s*[^-]{2,25}$", "", title).strip()
        try:
            published = datetime.strptime(pub.group(1), "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        except Exception:
            published = datetime.now(timezone.utc)
        items.append({
            "id": link, "he_title": he_title, "url": link,
            "source": source, "published": published.isoformat(),
        })
    return items

def fetch_govil_direct() -> list[dict]:
    """Попытка прямой выборки с ленты Минздрава. При Cloudflare-блоке тихо отдаёт [] .
    Если когда-то начнёт проходить (или снимут блок) — источник заработает автоматически."""
    try:
        raw = _get("https://www.gov.il/he/departments/topics/food-recall/govil-landing-page", timeout=20)
        text = raw.decode("utf-8", "ignore")
        if "Just a moment" in text or len(text) < 20000:  # челлендж или пустышка
            return []
        out = []
        for m in re.finditer(r'href="(https://www\.gov\.il/he/pages/(?:rcl|0[0-9]{6})[^"]*)"[^>]*>([^<]{15,300})', text):
            out.append({"id": m.group(1), "he_title": _clean(m.group(2)), "url": m.group(1),
                        "source": "Gov.il (Минздрав)", "published": datetime.now(timezone.utc).isoformat()})
        return out
    except Exception:
        return []
