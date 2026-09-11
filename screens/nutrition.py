import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.nutrition_calc import (
    DAILY_TARGETS,
    NUTRIENT_LABELS,
    NUTRIENTS,
    calculate_fulfillment,
    calculate_nutrition,
    load_nutrition_data,
)

st.title("📊 栄養分析")

if "ingredients" not in st.session_state or not st.session_state.ingredients:
    st.warning("まだ食材が登録されていません。「スキャン」画面で写真から食材を認識してください。")
    st.stop()

st.write("スキャンした食材から、今日摂れそうな栄養素を計算します。")

try:
    nutrition_df = load_nutrition_data()
    totals, unmatched = calculate_nutrition(st.session_state.ingredients, nutrition_df)
    fulfillment = calculate_fulfillment(totals)
except Exception as e:
    st.error("栄養データの読み込みに失敗しました。data/nutrition_data.csv の場所を確認してください。")
    st.exception(e)
    st.stop()

st.session_state["nutrition_fulfillment"] = fulfillment
st.session_state["nutrition_totals"] = totals

if unmatched:
    st.info(
        "以下の食材はデータベースに見つからなかったため、計算から除外されています: "
        + "、".join(unmatched)
    )

# ---- レーダーチャート ----
labels = [NUTRIENT_LABELS[n] for n in NUTRIENTS]
values = [min(fulfillment[n], 150) for n in NUTRIENTS]  # 見やすさのため150%で頭打ち

fig = go.Figure()
fig.add_trace(
    go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        name="充足率(%)",
    )
)
fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 150])),
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

# ---- 不足している栄養素トップ3 ----
st.subheader("不足している栄養素 トップ3")
sorted_nutrients = sorted(fulfillment.items(), key=lambda x: x[1])
top3 = sorted_nutrients[:3]

cols = st.columns(3)
for col, (n, pct) in zip(cols, top3):
    with col:
        st.metric(NUTRIENT_LABELS[n], f"{pct}%")

st.caption("不足栄養素を考慮したレシピは「レシピ提案」画面で提案してもらえます。")

# ---- 詳細テーブル ----
with st.expander("すべての栄養素の詳細を見る"):
    detail_rows = [
        {
            "栄養素": NUTRIENT_LABELS[n],
            "摂取量": round(totals[n], 1),
            "目標量": DAILY_TARGETS[n],
            "充足率": f"{fulfillment[n]}%",
        }
        for n in NUTRIENTS
    ]
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
