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

# 成人の1日あたりの目安量（簡易版）。
# 実際の「日本人の食事摂取基準」は性別・年齢・活動量によって細かく分かれているが、
# フェーズ3ではMVPとして、平均的な成人の目安値1セットのみを採用している。
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

# AIの認識結果が表記ゆれする場合に備えた簡易的な言い換え辞書。
# 完全ではないが、よくあるパターンだけ先にデータベースの表記へ揃えておく。
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
    """表記ゆれをデータベース側の表記に近づける"""
    for alias, canonical in ALIASES.items():
        if alias in name:
            return name.replace(alias, canonical)
    return name


def load_nutrition_data():
    """食品成分データ(簡易版)をCSVから読み込む"""
    return pd.read_csv("data/nutrition_data.csv")


def parse_quantity_to_grams(quantity_text, unit_weight_g):
    """AIが返した「3個」「500ml」のような文字列を、おおよそのグラム数に変換する"""
    if not quantity_text:
        return 100.0  # 情報が無い場合は標準的な1食分とみなす

    match = re.search(r"([\d.]+)\s*([^\d.\s]*)", str(quantity_text))
    if not match:
        return 100.0

    number = float(match.group(1))
    unit = match.group(2)

    if unit in ("g", "グラム"):
        return number
    if unit in ("ml", "ミリリットル"):
        return number  # 液体は 1ml ≒ 1g として簡易換算
    if unit == "大さじ":
        return number * 15
    if unit in COUNT_UNITS:
        base = unit_weight_g if pd.notna(unit_weight_g) else 100
        return number * base

    # 単位が認識できない場合は、数値をそのままグラムとみなす
    return number


def match_ingredient(name, nutrition_df):
    """食材名を、データベースの中から部分一致で探す"""
    for _, row in nutrition_df.iterrows():
        if row["name"] in name or name in row["name"]:
            return row
    return None


def calculate_nutrition(ingredients, nutrition_df):
    """食材リストから、栄養素の合計とマッチしなかった食材名を計算する"""
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
    """目標量に対する充足率(%)を、栄養素ごとに計算する"""
    fulfillment = {}
    for n in NUTRIENTS:
        target = DAILY_TARGETS[n]
        fulfillment[n] = round(totals[n] / target * 100, 1)
    return fulfillment
