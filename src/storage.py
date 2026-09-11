# -*- coding: utf-8 -*-
import json, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "db.json")

def load() -> dict:
    if os.path.exists(DB_PATH):
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"items": {}, "bootstrapped": False}

def save(db: dict):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1, sort_keys=True)

def is_new(db: dict, item_id: str) -> bool:
    return item_id not in db["items"]

def add(db: dict, card: dict, sent: bool):
    db["items"][card["id"]] = {
        "he_title": card["he_title"], "title_ru": card["title_ru"],
        "reason_ru": card["reason_ru"], "category_ru": card["category_ru"],
        "baby": card["baby"], "source": card["source"], "url": card["url"],
        "published": card["published"], "sent": sent,
        "photo_url": card.get("photo_url"), 
        "batches": card.get("batches", []),
        "dates": card.get("dates", []),
        "barcodes": card.get("barcodes", []),
        "maker": card.get("maker"),
    }
