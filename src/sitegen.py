# -*- coding: utf-8 -*-
"""Каталог site/index.html: счётчики, поиск по продукту (клиентский JS), фильтры категорий + карточки."""
import os, html, json
from cards import site_html, _style

SITE_DIR = os.path.join(os.path.dirname(__file__), "..", "site")

def slugify(item_id: str) -> str:
    import re
    s = re.sub(r"https?://", "", item_id)
    s = re.sub(r"[^a-zA-Z0-9-]", "-", s).strip("-")
    return s[-60:]

def generate(cards: list[dict], site_url_base: str = ""):
    os.makedirs(SITE_DIR, exist_ok=True)
    cards = sorted(cards, key=lambda x: x["published"], reverse=True)
    data = []
    rows = []
    for c in cards:
        fn = slugify(c["id"]) + ".html"
        with open(os.path.join(SITE_DIR, fn), "w", encoding="utf-8") as f:
            f.write(site_html(c, site_url_base))

        icon, color, bg = _style(c["category_ru"])
        badge = "👶" if c["baby"] else icon
        data.append({
            "t": c["title_ru"], "f": fn, "cat": c["category_ru"],
            "d": c["pub_short"], "b": badge, "baby": bool(c["baby"]),
            "r": c["reason_ru"] if c.get("reason_ru") else "",
            "id": c["id"], "title": c["title_ru"], "file": fn, "date": c["pub_short"],
            "category": c["category_ru"], "reason": c["reason_ru"], "product": c["product"],
            "brands": c["brands"], "barcodes": c.get("barcodes", []),
            "batches": c.get("batches", []), "dates": c.get("dates", []),
            "source": c.get("source_ru", c["source"]),
        })
        rows.append(f'<tr data-cat="{html.escape(c["category_ru"])}" data-text="{html.escape((c["title_ru"]+" "+c["reason_ru"]).lower())}">'
                    f'<td style="padding:10px 10px;border-bottom:1px solid #e8edf2;font-size:15px;">{badge} '
                    f'<a href="{fn}" style="color:#1d4ed8;text-decoration:none;font-weight:600;">{html.escape(c["title_ru"])}</a>'
                    f'<div style="font-size:12px;color:#5a6b7c;margin-top:3px;">{c["pub_short"]} · {html.escape(c.get("source_ru", c["source"]))}</div></td></tr>')
    n_baby = sum(1 for d in data if d["baby"])
    with open(os.path.join(SITE_DIR, "otzyvy.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    idx = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Отзывы Израиль — изъятия продукции на русском</title>
<meta name="description" content="Все отзывы (изъятия) продуктов в Израиле на русском языке: поиск по продукту, партии, даты, причины. Обновляется автоматически каждые 20 минут.">
</head><body style="margin:0;background:#f1f4f8;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#111c2b;">
<div style="max-width:760px;margin:0 auto;padding:24px 14px 40px;">
<h1 style="font-size:26px;margin:0 0 4px;">🚨 Отзывы Израиль</h1>
<p style="color:#3a4a5a;margin:4px 0 14px;line-height:1.5;">Все изъятия продукции — на русском, автоматически из официальных источников.
Всего в базе: <b>{len(cards)}</b> (детских: <b>{n_baby}</b>). Обновление каждые 20 минут.</p>
<div style="background:#fff;border:1px solid #e2e7ec;border-radius:14px;padding:14px;margin-bottom:14px;">
<input id="q" type="search" placeholder="🔍 Проверьте продукт: нутрилон, тхина, кукуруза…" style="width:100%;box-sizing:border-box;font-size:16px;padding:11px 14px;border:2px solid #cbd5e1;border-radius:10px;">
<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;" id="chips"></div>
</div>
<table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e7ec;border-radius:14px;overflow:hidden;" id="tbl">
{''.join(rows)}
</table>
<p id="empty" style="display:none;text-align:center;color:#5a6b7c;padding:20px;">Ничего не найдено — такого продукта в базе отзывов нет (это хорошо 🙂)</p>
<p style="font-size:12px;color:#5a6b7c;">Источники: Минздрав Израиля (Gov.il), Ynet и др. Справочная информация. Подписка на пуши — Telegram-бот «Отзывы Израиль».</p>
</div>
<script>
var q=document.getElementById('q'),tbl=document.getElementById('tbl'),empty=document.getElementById('empty');
var cats=[].slice.call(tbl.querySelectorAll('tr')).map(function(r){{return r.getAttribute('data-cat')}});
cats=[...new Set(cats)];
var chips=document.getElementById('chips'),active='Все';
function mkchip(name){{var b=document.createElement('button');b.textContent=name;
b.style.cssText='padding:6px 12px;border-radius:999px;border:1px solid #cbd5e1;background:'+(name===active?'#1d4ed8':'#fff')+';color:'+(name===active?'#fff':'#1e293b')+';font-size:13px;cursor:pointer;';
b.onclick=function(){{active=name;[].forEach.call(chips.children,function(x){{x.style.background=x.textContent===active?'#1d4ed8':'#fff';x.style.color=x.textContent===active?'#fff':'#1e293b';}});filter();}};
chips.appendChild(b);}}
mkchip('Все');cats.forEach(mkchip);mkchip('👶 Детское');
function filter(){{
var s=q.value.toLowerCase().trim(),n=0;
[].forEach.call(tbl.querySelectorAll('tr'),function(r){{
var okCat=(active==='Все')||(active==='👶 Детское'&&r.getAttribute('data-cat')==='детское питание')||(r.getAttribute('data-cat')===active);
var okTxt=!s||r.getAttribute('data-text').indexOf(s)>=0;
r.style.display=(okCat&&okTxt)?'':'none';if(okCat&&okTxt)n++;}});
empty.style.display=n?'none':'block';}}
q.addEventListener('input',filter);
</script></body></html>"""
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(idx)
