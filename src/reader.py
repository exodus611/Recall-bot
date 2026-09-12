# -*- coding: utf-8 -*-
"""Чтение статьи через публичный ридер r.jina.ai (исполняет JS, отдаёт текст).
Нужен, чтобы: (1) раскрыть ссылку Google News -> прямой URL статьи,
(2) прочитать текст сайта, который блокирует роботов (Israel Hayom и др.).
Без ключей, публичный сервис. Любая ошибка -> возврат None (бот молча деградирует)."""
import re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) recall-bot/1.0"}

def read_via_jina(url: str, timeout: int = 50):
    try:
        req = urllib.request.Request("https://r.jina.ai/" + url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", "ignore")
        final_url = None
        m = re.search(r"^URL Source:\s*(\S+)", text, re.M)
        if m: final_url = m.group(1).strip()
        return final_url, text
    except Exception:
        return None, None

def strip_md(text: str) -> str:
    """Убрать markdown-разметку из выдачи ридера."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)   # ссылки -> текст
    text = re.sub(r"[*_#>`]", " ", text)
    return re.sub(r"\s+", " ", text)
