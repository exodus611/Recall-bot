# -*- coding: utf-8 -*-
"""Отправка в Telegram: ТОЛЬКО текст sendMessage (без картинок третьих лиц).
Без токена — dry-run (печать в консоль)."""
import json, os, urllib.request
API = "https://api.telegram.org/bot{token}/sendMessage"

def deliver(token, chat_id, text, photo_url=None, dry=False):
    """photo_url игнорируется специально: карточка текстовая, медиа третьих лиц не используем."""
    if dry or not token or not chat_id:
        print("--- DRY-RUN ---\n" + text)
        return False
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                          "disable_web_page_preview": False}).encode()
    req = urllib.request.Request(API.format(token=token), data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        ok = json.load(r).get("ok", False)
    if not ok: raise RuntimeError("Telegram API отклонил")
    return True

def send(token, chat_id, text, dry=False):
    return deliver(token, chat_id, text, None, dry)
