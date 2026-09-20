import re
import pandas as pd

NUTRIENTS = [
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carb_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_c_mg",
    "fiber_g",
]

NUTRIENT_LABELS = {
    "energy_kcal": "エネルギー",
    "protein_g": "タンパク質",
    "fat_g": "脂質",
    "carb_g": "炭水化物",
    "iron_mg": "鉄分",
    "calcium_mg": "カルシウム",
    "vitamin_c_mg": "ビタミンC",
    "fiber_g": "食物繊維",
}

NUTRIENT_UNITS = {
    "energy_kcal": "kcal",
    "protein_g": "g",
    "fat_g": "g",
    "carb_g": "g",
    "iron_mg": "mg",
    "calcium_mg": "mg",
    "vitamin_c_mg": "mg",
    "fiber_g": "g",
}

DAILY_TARGETS = {
    "energy_kcal": 2200,
    "protein_g": 60,
    "fat_g": 60,
    "carb_g": 320,
    "iron_mg": 7.5,
    "calcium_mg": 650,
    "vitamin_c_mg": 100,
    "fiber_g": 19,
}

COUNT_UNITS = ("個", "本", "枚", "パック", "缶", "丁", "袋", "株", "玉", "杯", "切れ", "束")

ALIASES = {
    "たまご": "卵",
    "玉子": "卵",
    "生卵": "卵",
    "ミルク": "牛乳",
    "白米": "米・ごはん",
    "ごはん": "米・ごはん",
    "ご飯": "米・ごはん",
    "パン": "食パン",
    "キュウリ": "きゅうり",
    "人参": "にんじん",
    "ニンジン": "にんじん",
    "ミニトマト": "トマト",
    "牛乳パック": "牛乳",
    "とうふ": "豆腐",
    "なっとう": "納豆",
    "鮭": "さけ",
    "サケ": "さけ",
    "鯖": "さば",
    "サバ": "さば",
}


def normalize_ingredient_name(name):
    for alias, canonical in ALIASES.items():
        if alias in name:
            return name.replace(alias, canonical)
    return name


def load_nutrition_data():
    return pd.read_csv("data/nutrition_data.csv")


def parse_quantity_to_grams(quantity_text, unit_weight_g):
    if not quantity_text:
        return 100.0

    match = re.search(r"([\d.]+)\s*([^\d.\s]*)", str(quantity_text))
    if not match:
        return 100.0

    number = float(match.group(1))
    unit = match.group(2)

    if unit in ("g", "グラム"):
        return number
    if unit in ("ml", "ミリリットル"):
        return number
    if unit == "大さじ":
        return number * 15
    if unit in COUNT_UNITS:
        base = unit_weight_g if pd.notna(unit_weight_g) else 100
        return number * base

    return number


def match_ingredient(name, nutrition_df):
    for _, row in nutrition_df.iterrows():
        if row["name"] in name or name in row["name"]:
            return row
    return None


def calculate_nutrition(ingredients, nutrition_df):
    totals = {n: 0.0 for n in NUTRIENTS}
    unmatched = []

    for item in ingredients:
        name = str(item.get("name", "")).strip()
        quantity_text = item.get("quantity", "")

        if not name:
            continue

        normalized_name = normalize_ingredient_name(name)
        row = match_ingredient(normalized_name, nutrition_df)
        if row is None:
            unmatched.append(name)
            continue

        grams = parse_quantity_to_grams(quantity_text, row.get("unit_weight_g"))
        ratio = grams / 100.0

        for n in NUTRIENTS:
            totals[n] += row[n] * ratio

    return totals, unmatched


def calculate_fulfillment(totals):
    fulfillment = {}
    for n in NUTRIENTS:
        target = DAILY_TARGETS[n]
        fulfillment[n] = round(totals[n] / target * 100, 1)
    return fulfillment