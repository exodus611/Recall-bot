# -*- coding: utf-8 -*-
"""Официальные RSS-фиды израильских СМИ с прямыми ссылками (обогащение + детекция)."""
import re, html, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) recall-bot/1.0"}
FEEDS = {
    "Ynet": "https://www.ynet.co.il/Integration/StoryRss2.xml",
    "Ynet Health": "https://www.ynet.co.il/Integration/StoryRss3084.xml",
}
import urllib.parse
Q = urllib.parse.quote("ריקול OR החזרה יזומה")
FEEDS["Ynet Search"] = f"https://news.google.com/rss/search?q={Q}+site:ynet.co.il&hl=he&gl=IL&ceid=IL:he"

def _clean(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def fetch() -> list[dict]:
    out = []
    for src, u in FEEDS.items():
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read().decode("utf-8", "ignore")
        except Exception:
            continue
        for b in re.findall(r"<item>(.*?)</item>", raw, re.S):
            if not re.search(r"ריקול|החזרה יזומה|קריאה להחזרה", b):
                continue
            t = re.search(r"<title>(.*?)</title>", b, re.S).group(1)
            l = re.search(r"<link>(.*?)</link>", b, re.S).group(1).strip()
            out.append({"id": l, "he_title": _clean(t), "url": l,
                        "source": src, "published": datetime.now(timezone.utc).isoformat()})
    return out
