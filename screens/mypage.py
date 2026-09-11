from collections import Counter

import streamlit as st
from utils.firebase_client import get_all_meal_logs, get_firestore_client
from utils.nutrition_calc import NUTRIENT_LABELS, NUTRIENT_UNITS, NUTRIENTS

st.title("👤 マイページ")
st.write(f'ログイン中のユーザー: **{st.session_state["name"]}**')

username = st.session_state["username"]

# ============================================================
# 記録サマリー
# ============================================================
st.divider()
st.subheader("📊 記録サマリー")

try:
    all_logs = get_all_meal_logs(username)

    if not all_logs:
        st.info("まだ食事の記録がありません。「メモ」画面から記録してみてください。")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("これまでの記録数", f"{len(all_logs)}件")
        with col2:
            st.metric("最後に記録した日", all_logs[0].get("date", "-"))

        st.markdown("**よく作っている料理 トップ3**")
        title_counts = Counter(log.get("title", "") for log in all_logs if log.get("title"))
        for title, count in title_counts.most_common(3):
            st.write(f"- {title}（{count}回）")

        # ---- 記録から分かる栄養摂取の累計（カロリー・栄養素が記録されている分のみ） ----
        logs_with_nutrition = [log for log in all_logs if log.get("nutrition")]
        if logs_with_nutrition:
            st.markdown("**記録された食事からの累計摂取量**")
            totals = {n: 0.0 for n in NUTRIENTS}
            for log in logs_with_nutrition:
                nutrition = log["nutrition"]
                for n in NUTRIENTS:
                    totals[n] += nutrition.get(n, 0)

            st.metric("累計摂取カロリー", f"{round(totals['energy_kcal'])} kcal")

            with st.expander("栄養素ごとの累計を見る"):
                for n in NUTRIENTS:
                    if n == "energy_kcal":
                        continue
                    st.write(f"{NUTRIENT_LABELS[n]}: {round(totals[n], 1)}{NUTRIENT_UNITS[n]}")

            st.caption(
                f"※カロリー・栄養素は、「レシピ提案」から記録した{len(logs_with_nutrition)}件の食事のみ集計しています"
                "（自由入力で記録したものは対象外です）。"
            )

except Exception as e:
    st.error("記録の読み込みに失敗しました。Firebaseの設定を確認してください。")
    st.exception(e)

# ============================================================
# Firebase接続テスト
# ============================================================
st.divider()
st.subheader("🔧 Firebase接続テスト")

if st.button("Firestoreに接続してテストデータを書き込む"):
    try:
        db = get_firestore_client()

        db.collection("users").document(username).set(
            {
                "name": st.session_state["name"],
                "email": st.session_state.get("email", ""),
            },
            merge=True,
        )

        doc = db.collection("users").document(username).get()
        st.success("Firestoreへの接続・書き込み・読み込みに成功しました 🎉")
        st.json(doc.to_dict())
    except Exception as e:
        st.error("Firestoreへの接続に失敗しました。secrets.tomlの設定を確認してください。")
        st.exception(e)
