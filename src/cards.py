# -*- coding: utf-8 -*-
"""Тексты и вёрстка: сообщение для Telegram + страница-карточка для сайта."""

STYLE = {
    "детское питание": ("👶", "#7c3aed", "#f5f0ff"),
    "мясо/рыба":       ("🥩", "#b91c1c", "#fff1f0"),
    "молочные продукты":("🧀", "#a16207", "#fffbeb"),
    "сладости/выпечка": ("🍩", "#be185d", "#fdf2f8"),
    "овощи/фрукты/яйца":("🥬", "#15803d", "#f0fdf4"),
    "БАДы/витамины":   ("💊", "#0e7490", "#ecfeff"),
    "напитки":         ("🥤", "#1d4ed8", "#eff6ff"),
    "бакалея/консервы":("🥫", "#374151", "#f9fafb"),
    "не определена":   ("📦", "#475569", "#f8fafc"),
}

def _style(cat):
    return STYLE.get(cat, STYLE["не определена"])

def _badge_list(c):
    b = []
    if c.get("baby"): b.append("👶 ДЕТСКОЕ ПИТАНИЕ")
    if "аллерген" in c.get("reason_ru", ""): b.append("⚠️ АЛЛЕРГЕН")
    if any(w in c.get("reason_ru", "") for w in ("сальмонелла", "листерия", "бактер")): b.append("🦠 БАКТЕРИИ")
    if any(w in c.get("reason_ru", "") for w in ("металл", "посторонний предмет", "стекл")): b.append("🔩 ПОСТОРОННИЙ ПРЕДМЕТ")
    return b

def telegram_text(c: dict, site_url: str = "") -> str:
    icon, _, _ = _style(c["category_ru"])
    head = "👶❗ ИЗЪЯТИЕ ДЕТСКОГО ПИТАНИЯ — Recall (Израиль)" if c["baby"] else f"{icon} ИЗЪЯТИЕ ПРОДУКТА — Recall (Израиль)"
    lines = [f"<b>{head}</b>", ""]
    if c.get("product") != "— (в заголовке не назван)":
        lines.append(f"📦 <b>Продукт:</b> {c['product']}")
    if c["brands"] != "—":
        lines.append(f"🏷 <b>Бренд:</b> {c['brands']}")
    if c.get("reason_ru"):
        lines.append(f"⚠️ <b>Причина:</b> {c['reason_ru']}")
    if c.get("category_ru") and c["category_ru"] != "не определена":
        lines.append(f"🗂 <b>Категория:</b> {c['category_ru']}")
    if c.get("barcodes"):
        lines.append("🔖 <b>Штрих-код (баркод):</b> " + ", ".join(c["barcodes"]))
    if c.get("batches"):
        lines.append("🏷 <b>Партии:</b> " + ", ".join(c["batches"]))
    if c.get("dates"):
        lines.append("📅 <b>Годен до:</b> " + ", ".join(c["dates"]))
    if c.get("maker"):
        lines.append(f"🏭 <b>Производитель/импортёр:</b> {c['maker']}")
    lines += [
        f"📅 <b>Опубликовано:</b> {c['pub_short']} · 📰 {c.get('source_ru', c['source'])}",
        "",
        "✅ <b>Что делать:</b> проверьте продукт дома; отозванный товар примет магазин (вернут деньги).",
        f"🔗 {'Оригинал на иврите' if c.get('orig_lang') == 'иврит' else 'Оригинал на русском'} — там фото, партии и детали: {c['url']}",
    ]
    if site_url:
        lines.append(f"🌐 Все отзывы на русском: {site_url}")
    lines += ["", "<i>Автоперевод официального объявления по словарю, без ИИ. Бот ничего не собирает о вас.</i>"]
    return "\n".join(lines)

def site_html(c: dict, site_url_base: str = "") -> str:
    icon, color, bg = _style(c["category_ru"])
    reason_line = f'<p style="margin:6px 0;">⚠️ <b>Причина изъятия:</b> {c["reason_ru"]}</p>' if c.get("reason_ru") else ""
    cat_line = f'<p style="margin:6px 0;">🗂 <b>Категория:</b> {c["category_ru"]}</p>' if c.get("category_ru") and c["category_ru"] != "не определена" else ""
    brand_line = f'<p style="margin:6px 0;">🏷 <b>Бренд:</b> {c["brands"]}</p>' if c.get("brands") and c["brands"] != "—" else ""
    badges = "".join(
        f'<span style="background:{color};color:#fff;border-radius:999px;padding:4px 12px;font-size:12px;font-weight:700;">{b}</span>'
        for b in _badge_list(c)) or f'<span style="background:{color};color:#fff;border-radius:999px;padding:4px 12px;font-size:12px;font-weight:700;">ОТЗЫВ</span>'
    # Фото — только если есть прямая ссылка на статью источника (og:image, с подписью автора фото).
    if c.get("photo_url"):
        photo = (f'<img src="{c["photo_url"]}" alt="Фото продукта" loading="lazy" '
                 'style="max-width:100%;max-height:320px;border-radius:12px;border:1px solid #e2e7ec;">'
                 f'<div style="font-size:12px;color:#5a6b7c;margin-top:4px;">Фото: {c.get("source_ru", c["source"])}</div>')
    else:
        photo = (f'<div style="height:130px;border-radius:12px;background:{bg};display:flex;align-items:center;'
                 f'justify-content:center;font-size:60px;border:1px dashed #cbd5e1;">{icon}</div>')
    data_cells = []
    if c.get("barcodes"):
        data_cells.append(f'<div style="flex:1;min-width:200px;background:{bg};border-radius:10px;padding:12px;">'
                          f'<div style="font-size:12px;color:#5a6b7c;">ШТРИХ-КОД (БАРКОД)</div>'
                          f'<div style="font-family:monospace;font-size:14px;font-weight:700;">{", ".join(c["barcodes"])}</div></div>')
    if c.get("batches"):
        data_cells.append(f'<div style="flex:1;min-width:200px;background:{bg};border-radius:10px;padding:12px;">'
                          f'<div style="font-size:12px;color:#5a6b7c;">НОМЕРА ПАРТИЙ</div>'
                          f'<div style="font-family:monospace;font-size:14px;font-weight:700;">{", ".join(c["batches"])}</div></div>')
    if c.get("dates"):
        data_cells.append(f'<div style="flex:1;min-width:200px;background:{bg};border-radius:10px;padding:12px;">'
                          f'<div style="font-size:12px;color:#5a6b7c;">ГОДЕН ДО</div>'
                          f'<div style="font-family:monospace;font-size:14px;font-weight:700;">{", ".join(c["dates"])}</div></div>')
    batches = ('<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;">' + "".join(data_cells) + '</div>') if data_cells else ""
    maker_line = f'<p style="margin:6px 0;">🏭 <b>Производитель/импортёр:</b> {c["maker"]}</p>' if c.get("maker") else ""
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{c['title_ru']} — Отзывы Израиль</title>
<meta name="description" content="Отзыв продукции в Израиле: {c['product']}. Причина: {c['reason_ru']}. Партии, даты, что делать — на русском.">
</head><body style="margin:0;background:#f1f4f8;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#111c2b;">
<div style="max-width:680px;margin:0 auto;padding:20px 14px 40px;">
<div style="font-size:13px;margin-bottom:14px;"><a href="index.html" style="color:#2b5278;text-decoration:none;">← Все отзывы</a></div>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">{badges}</div>
<h1 style="font-size:26px;line-height:1.25;margin:0 0 6px;">{c['title_ru']}</h1>
<div style="color:#5a6b7c;font-size:14px;margin-bottom:16px;">{c['pub_short']} · источник: {c.get('source_ru', c['source'])}</div>
<div style="background:#fff;border:1px solid #e2e7ec;border-radius:16px;padding:18px;">
<div style="text-align:center;margin-bottom:14px;">{photo}</div>
{batches}{maker_line}
<div style="margin-top:14px;font-size:16px;line-height:1.7;">
{reason_line}{cat_line}{brand_line}
<div style="background:{bg};border-radius:10px;padding:12px 14px;margin-top:10px;">
<b>Что делать:</b>
<ol style="margin:6px 0 0 18px;padding:0;">
<li>Найдите продукт дома и сверьте партию/срок с указанными выше или в оригинале.</li>
<li>Не употребляйте, если совпало — верните в магазин, деньги обязаны вернуть.</li>
<li>При недомогании после употребления обратитесь к врачу (в экстренных случаях 101).</li>
</ol></div>
<p style="background:#eef4ea;border-radius:10px;padding:10px 12px;margin-top:12px;">📲 <b>Хотите узнавать об изъятиях первым?</b> Подпишитесь на Telegram-бота «Отзывы Израиль» — {site_url_base or '(ссылка в шапке каталога)'}</p>
<p style="font-size:12px;color:#5a6b7c;">Автоперевод официального объявления по словарю, без ИИ. Первоисточник: <a href="{c['url']}" style="color:#2b5278;">{c.get('source_ru', c['source'])}</a>. Справочная информация, не медицинская консультация.</p>
</div></div></div></body></html>"""
