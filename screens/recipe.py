import json
import streamlit as st
from google.genai import types
from utils.gemini_client import get_gemini_client
from utils.nutrition_calc import (
    NUTRIENT_LABELS,
    calculate_fulfillment,
    calculate_nutrition,
    load_nutrition_data,
)

st.title("🍳 レシピ提案")

if "ingredients" not in st.session_state or not st.session_state.ingredients:
    st.warning("まだ食材が登録されていません。「スキャン」画面で写真から食材を認識してください。")
    st.stop()

# ---- 不足栄養素トップ3を取得（栄養分析画面と同じロジックで計算し直す） ----
top3_labels = []
try:
    nutrition_df = load_nutrition_data()
    totals, _ = calculate_nutrition(st.session_state.ingredients, nutrition_df)
    fulfillment = calculate_fulfillment(totals)
    top3 = sorted(fulfillment.items(), key=lambda x: x[1])[:3]
    top3_labels = [NUTRIENT_LABELS[n] for n, _ in top3]
except Exception:
    st.info("栄養情報の計算に失敗したため、栄養素を考慮せずレシピを提案します。")

st.write("手持ちの食材と、不足している栄養素をもとに、AIがレシピを3つ提案します。")
if top3_labels:
    st.caption(f"現在、不足しがちな栄養素: {'、'.join(top3_labels)}")

if st.button("レシピを提案してもらう"):
    with st.spinner("AIがレシピを考えています..."):
        try:
            client = get_gemini_client()

            ingredient_lines = "\n".join(
                f"- {i.get('name', '')}（{i.get('quantity', '')}）"
                for i in st.session_state.ingredients
            )
            deficient_text = "、".join(top3_labels) if top3_labels else "特になし"

            prompt = f"""以下は冷蔵庫にある食材の一覧です。

{ingredient_lines}

現在不足しがちな栄養素は次の通りです: {deficient_text}

手持ちの食材をできるだけ優先的に使い、不足している栄養素を補えるような、
調理時間15分以内で作れる料理を3つ提案してください。
それぞれの料理について、使用する食材（手持ちのものか、追加で買う必要があるものかを区別）、
その食材をどれくらい使うか（例: 2個、100g、大さじ1 など）、
簡単な手順、その料理で補える栄養素を教えてください。
すべて日本語で答えてください。"""

            response_schema = {
                "type": "object",
                "properties": {
                    "recipes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "ingredients": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "quantity": {"type": "string"},
                                            "source": {
                                                "type": "string",
                                                "enum": ["手持ち", "追加購入"],
                                            },
                                        },
                                        "required": ["name", "quantity", "source"],
                                    },
                                },
                                "steps": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "nutrients_covered": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["title", "ingredients", "steps", "nutrients_covered"],
                        },
                    }
                },
                "required": ["recipes"],
            }

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=[prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )

            result = json.loads(response.text)
            recipes = result["recipes"]
            st.session_state["recipes"] = recipes

            shopping_items = []
            for recipe in recipes:
                for ing in recipe.get("ingredients", []):
                    if ing.get("source") == "追加購入":
                        item_name = ing.get("name", "")
                        if item_name and item_name not in shopping_items:
                            shopping_items.append(item_name)
            st.session_state["shopping_list"] = shopping_items

            st.success("レシピを提案しました。買い物メモも自動で更新されました。")

        except json.JSONDecodeError:
            st.error("AIの応答をうまく読み取れませんでした。もう一度お試しください。")
        except Exception as e:
            st.error("レシピの提案中にエラーが発生しました。通信状況を確認し、もう一度お試しください。")
            st.exception(e)

if st.session_state.get("recipes"):
    st.divider()
    cols = st.columns(3)
    for col, recipe in zip(cols, st.session_state["recipes"]):
        with col:
            st.subheader(recipe.get("title", "レシピ"))

            st.markdown("**使う食材**")
            for ing in recipe.get("ingredients", []):
                mark = "🛒" if ing.get("source") == "追加購入" else "✅"
                st.write(f"{mark} {ing.get('name', '')}（{ing.get('quantity', '')}・{ing.get('source', '')}）")

            st.markdown("**作り方**")
            for i, step in enumerate(recipe.get("steps", []), start=1):
                st.write(f"{i}. {step}")

            if recipe.get("nutrients_covered"):
                st.markdown("**補える栄養素**")
                st.write("、".join(recipe["nutrients_covered"]))

    st.caption("作った料理は「メモ」画面から記録できます（摂取カロリー・栄養素も自動で計算されます）。")
