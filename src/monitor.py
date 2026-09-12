# -*- coding: utf-8 -*-
"""Главный цикл: детекция (Google News RSS + прямые RSS СМИ) -> словарь -> обогащение
(фото+партии, если есть прямая ссылка) -> Telegram -> база -> сайт.
--bootstrap: первый запуск запоминает всё и ничего не публикует."""
import sys, os, time, argparse, re, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sources, ynet, translate, storage, tgsend, sitegen, cse
from reader import read_via_jina, strip_md
from extract import analyze
from yahoo_enrich import enrich
from cards import telegram_text

def heartbeat(url):
    if url:
        try: urllib.request.urlopen(url, timeout=15)
        except Exception as e: print("heartbeat fail:", e)

NOISE = re.compile(r"(האכלתי|אכלתי|בתי\b|שלי\b|עדיין בודקים|ראיון|דעה|בלוג)")
HARD  = re.compile(r"(ריקול|החזרה יזומה|קריאה להחזרה|משיכה מהמדפים|יורד מהמדפים|מושך מהמדפים)")

def relevant(he_title: str) -> bool:
    return bool(HARD.search(he_title)) and not bool(NOISE.search(he_title))

def norm(s):
    s = re.sub(r"[^\u05d0-\u05ea0-9a-zA-Z ]", " ", s)
    return set(w for w in s.split() if len(w) >= 3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bootstrap", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat  = os.environ.get("TELEGRAM_CHAT_ID", "")
    site  = os.environ.get("SITE_BASE_URL", "")
    hc    = os.environ.get("HEALTHCHECK_URL", "")
    dry   = args.dry_run or not (token and chat)

    db = storage.load()

    raw = sources.fetch_govil_direct() + sources.fetch_google_news() + ynet.fetch()
    seen, items = set(), []
    for it in raw:
        if not relevant(it["he_title"]): continue
        k = it["he_title"][:55]
        if k in seen: continue
        seen.add(k); items.append(it)
    print(f"публикаций об отзывах: {len(items)}")

    new = [it for it in items if storage.is_new(db, it["id"])]
    print(f"новых: {len(new)}")

    # для каждого нового gnews-итема ищем вариант с прямой ссылкой (для фото/партий)
    direct_pool = [it for it in items if "news.google.com" not in it["url"]]
    # приоритет ссылки: gov.il > прямая статья СМИ (свежая) > ссылка Google News
    def link_rank(u: str) -> int:
        if "gov.il" in u: return 0
        if "news.google.com" not in u: return 1
        return 2

    cards = []
    for it in new:
        c = translate.build_card(it)
        if "news.google.com" in c["url"]:
            direct = cse.resolve(c["he_title"])
            if direct:
                c["url"] = direct
                c["source"] = "прямая ссылка"
                c["source_ru"] = "оригинал объявления"
            tok = norm(c["he_title"])
            match = max(direct_pool, key=lambda d: len(tok & norm(d["he_title"])), default=None)
            if match and match is not None and len(tok & norm(match["he_title"])) >= 2:
                c["url"] = match["url"]
                c["source"] = match["source"]
                c["source_ru"] = translate.src_ru(match["source"])
        e = enrich(c["url"])
        c.update(photo_url=e["photo_url"], batches=e["batches"][:6], dates=e["dates"], barcodes=e.get("barcodes", []), maker=e.get("maker"))
        # --- схематичный разбор статьи (всегда, даже без ключей CSE) ---
        read_url = c["url"]
        if "news.google.com" in read_url:
            read_url = cse.resolve(c["he_title"]) or ""
        if read_url:
            _, text = read_via_jina(read_url)
            if text:
                d = analyze(strip_md(text))
                if d.get("reason_ru") and not c["guessed"]:
                    c["reason_ru"] = d["reason_ru"]; c["guessed"] = True
                if d.get("category_ru") and (c["category_ru"] == "не определена"):
                    c["category_ru"] = d["category_ru"]; c["baby"] = c["baby"] or d.get("baby", False)
                if d.get("barcode"):
                    c["barcodes"] = sorted(set(c.get("barcodes", []) + d["barcode"]))[:8]
                if d.get("exp"):
                    c["dates"] = (c.get("dates", []) + [x for x in d["exp"] if x not in c.get("dates", [])])[:8]
                if d.get("maker") and (not c.get("maker") or c["maker"] in (None, "—")):
                    c["maker"] = d["maker"]
                if d.get("brand") and c["brands"] in (None, "—"):
                    c["brands"] = d["brand"]
                if d.get("product") and c["product"] == "— (в заголовке не назван)":
                    c["product"] = d["product"]
                    c["title_ru"] = f"Изъятие: {d['product']} — {c['reason_ru']}" if c.get("reason_ru") else c["title_ru"]
        cards.append(c)

    if args.bootstrap and not db.get("bootstrapped"):
        for c in cards: storage.add(db, c, sent=False)
        db["bootstrapped"] = True
    else:
        for c in cards:
            try:
                tgsend.deliver(token, chat, telegram_text(c, site), c.get("photo_url"), dry)
                storage.add(db, c, sent=True)
                time.sleep(1.2)
            except Exception as e:
                storage.add(db, c, sent=False)
                print("ошибка отправки:", e)

    all_cards = []
    for k, v in db["items"].items():
        c = translate.build_card(v | {"id": k, "published": v["published"], "source": v["source"]})
        c["photo_url"] = v.get("photo_url"); c["batches"] = v.get("batches", []); c["dates"] = v.get("dates", []); c["barcodes"] = v.get("barcodes", []); c["maker"] = v.get("maker")
        all_cards.append(c)
    sitegen.generate(all_cards, site)
    storage.save(db)
    print(f"опубликовано: {sum(1 for c in cards if db['items'].get(c['id'], {}).get('sent'))}; всего в базе: {len(db['items'])}")
    heartbeat(hc)

if __name__ == "__main__":
    main()
