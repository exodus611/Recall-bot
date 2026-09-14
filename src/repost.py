# -*- coding: utf-8 -*-
"""Повторная публикация существующей карточки из базы (без дубликатов в базе).
Запуск: python src/repost.py --find ТЕКСТ  (ищет подстроку в заголовке/продукте/бренде)"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, translate, cards, tgsend

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--find", required=True, help="подстрока для поиска карточки")
    ap.add_argument("--site", default=os.environ.get("SITE_BASE_URL", "https://exodus611.github.io/Recall-bot/"))
    a = ap.parse_args()
    db = json.load(open("data/db.json"))
    hits = []
    for k, v in db["items"].items():
        hay = " ".join([str(v.get("he_title","")), str(v.get("title_ru","")), str(v.get("product","")), str(v.get("brands",""))])
        if a.find.lower() in hay.lower():
            v = dict(v); v["id"] = k
            c = translate.build_card(v)
            c["photo_url"] = v.get("photo_url"); c["maker"] = v.get("maker")
            for f in ("batches", "dates", "barcodes"):
                c[f] = v.get(f) or []
            hits.append((k, c))
    if not hits:
        print("карточка не найдена по:", a.find); sys.exit(1)
    k, c = hits[0]
    print("публикую:", c["title_ru"])
    token = os.environ.get("TELEGRAM_BOT_TOKEN", ""); chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    tgsend.deliver(token, chat, cards.telegram_text(c, a.site), None, dry=not token)
    print("отправлено" if token else "СУХОЙ РЕЖИМ (нет токена)")

if __name__ == "__main__":
    main()
