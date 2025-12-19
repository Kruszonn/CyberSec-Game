from __future__ import annotations

import json
import os
from dataclasses import dataclass


SAVE_PATH = os.path.join("data", "saves", "slot1.json")


def default_save() -> dict:
    return {
        "world": {"map": "city"},
        "player": {"x": 200.0, "y": 200.0},
        "trust": {},
        "scores": {
            "total": 0,
            "phishing": 0,
            "password": 0,
            "links": 0,
            "mfa": 0,
        },
        "completed": {
            "challenges": [],
        },
    }


def load_save() -> dict:
    if not os.path.exists(SAVE_PATH):
        return default_save()

    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # If corrupted, fall back safely.
        return default_save()

    # Light normalization
    base = default_save()
    base.update(data)

    if "world" not in base or not isinstance(base["world"], dict):
        base["world"] = {"map": "city"}
    if "map" not in base["world"]:
        base["world"]["map"] = "city"

    if "player" not in base or not isinstance(base["player"], dict):
        base["player"] = {"x": 200.0, "y": 200.0}

    if "trust" not in base or not isinstance(base["trust"], dict):
        base["trust"] = {}

    if "scores" not in base or not isinstance(base["scores"], dict):
        base["scores"] = default_save()["scores"]

    if "completed" not in base or not isinstance(base["completed"], dict):
        base["completed"] = default_save()["completed"]

    if "challenges" not in base["completed"] or not isinstance(base["completed"]["challenges"], list):
        base["completed"]["challenges"] = []

    return base


def save_game(data: dict) -> None:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
