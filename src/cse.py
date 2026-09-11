# -*- coding: utf-8 -*-
"""Резолв прямой ссылки статьи по заголовку через официальный Google Programmable
Search JSON API (бесплатный, 100 запросов/день). Нужны ключи:
GOOGLE_CSE_KEY, GOOGLE_CSE_CX (https://programmablesearchengine.google.com).
Нет ключей -> карточка остаётся текстовой со ссылкой Google News (работает для людей)."""
import json, os, urllib.parse, urllib.request

def resolve(he_title: str) -> str | None:
    key = os.environ.get("GOOGLE_CSE_KEY", "")
    cx = os.environ.get("GOOGLE_CSE_CX", "")
    if not (key and cx):
        return None
    q = urllib.parse.quote(he_title[:90])
    url = (f"https://www.googleapis.com/customsearch/v1?key={key}&cx={cx}"
           f"&q={q}&num=1")
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            items = json.load(r).get("items", [])
            return items[0]["link"] if items else None
    except Exception:
        return None
