from datetime import date

import pandas as pd
import streamlit as st
from utils.firebase_client import get_meal_logs, save_meal_log
from utils.nutrition_calc import (
    NUTRIENT_LABELS,
    NUTRIENT_UNITS,
    calculate_nutrition,
    load_nutrition_data,
)

st.title("📝 メモ（買い物・食べたもの）")

username = st.session_state["username"]

# ============================================================
# 買い物メモ
# ============================================================
st.header("🛒 買い物メモ")
st.write("「レシピ提案」でレシピを提案してもらうと、追加購入が必要な食材がここに自動で反映されます。")

shopping_list = st.session_state.get("shopping_list", [])

if not shopping_list:
    st.info("まだ買い物メモがありません。「レシピ提案」画面でレシピを提案してもらうと、ここに表示されます。")
else:
    df = pd.DataFrame({"食材": shopping_list, "購入済み": [False] * len(shopping_list)})

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"購入済み": st.column_config.CheckboxColumn("購入済み")},
        key="shopping_editor",
    )

    remaining = edited_df[~edited_df["購入済み"]]
    if len(remaining) == 0:
        st.success("すべて購入済みです 🎉")
    else:
        st.write(f"あと {len(remaining)} 品、購入が必要です。")

# ============================================================
# 食べたものメモ
# ============================================================
st.divider()
st.header("🍽 食べたものメモ")
st.write("実際に作った・食べた料理を記録できます。提案されたレシピを選ぶと、カロリーや栄養素も自動で記録されます。")

recipes = st.session_state.get("recipes", [])
recipe_titles = [r.get("title", "") for r in recipes]
options = recipe_titles + ["その他（自由入力）"]

with st.form("meal_log_form", clear_on_submit=True):
    selected = st.selectbox("何を作りましたか？", options) if recipe_titles else None
    free_text = st.text_input(
        "料理名を入力" if not recipe_titles else "「その他」を選んだ場合はこちらに入力",
    )
    log_date = st.date_input("日付", value=date.today())
    submitted = st.form_submit_button("記録する")

    if submitted:
        is_other = (not recipe_titles) or (selected == "その他（自由入力）")
        title = free_text if is_other else selected

        if not title:
            st.warning("料理名を入力してください。")
        else:
            nutrition_totals = None
            if not is_other:
                # 選んだレシピの食材リストから、カロリー・栄養素を計算する
                matched_recipe = next((r for r in recipes if r.get("title") == selected), None)
                if matched_recipe:
                    try:
                        nutrition_df = load_nutrition_data()
                        nutrition_totals, unmatched = calculate_nutrition(
                            matched_recipe.get("ingredients", []), nutrition_df
                        )
                        if unmatched:
                            st.caption(
                                "※一部の食材はデータベースに無かったため、栄養計算から除外されています: "
                                + "、".join(unmatched)
                            )
                    except Exception:
                        nutrition_totals = None
                        st.caption("※栄養計算に失敗したため、カロリー等は記録されませんでした。")

            try:
                save_meal_log(username, title, log_date.strftime("%Y-%m-%d"), nutrition_totals)
                if nutrition_totals:
                    kcal = round(nutrition_totals.get("energy_kcal", 0))
                    st.success(f"「{title}」を記録しました（約{kcal}kcal）。")
                else:
                    st.success(f"「{title}」を記録しました。")
            except Exception as e:
                st.error("記録の保存に失敗しました。Firebaseの設定を確認してください。")
                st.exception(e)

if not recipe_titles:
    st.caption("「レシピ提案」画面でレシピを提案してもらうと、カロリー・栄養素が自動計算されるようになります。")

st.subheader("直近の記録")
try:
    logs = get_meal_logs(username, limit=10)
    if not logs:
        st.write("まだ記録がありません。")
    else:
        log_rows = []
        for log in logs:
            nutrition = log.get("nutrition") or {}
            log_rows.append(
                {
                    "日付": log.get("date", ""),
                    "料理名": log.get("title", ""),
                    "カロリー": f"{round(nutrition['energy_kcal'])}kcal" if "energy_kcal" in nutrition else "-",
                }
            )
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

        with st.expander("直近の記録の栄養素の内訳を見る"):
            for log in logs:
                nutrition = log.get("nutrition")
                if not nutrition:
                    continue
                st.markdown(f"**{log.get('date', '')}　{log.get('title', '')}**")
                detail = ", ".join(
                    f"{NUTRIENT_LABELS[n]} {nutrition.get(n, 0)}{NUTRIENT_UNITS[n]}"
                    for n in NUTRIENT_LABELS
                    if n in nutrition
                )
                st.write(detail)
except Exception as e:
    st.error("記録の読み込みに失敗しました。Firebaseの設定を確認してください。")
    st.exception(e)
