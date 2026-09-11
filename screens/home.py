import pandas as pd
import streamlit as st
from utils.firebase_client import get_meal_logs

st.title("🏠 ホーム")
st.write(f'ようこそ、**{st.session_state["name"]}** さん')

st.divider()
st.subheader("📋 最近の食事記録")

username = st.session_state["username"]

try:
    logs = get_meal_logs(username, limit=5)
    if not logs:
        st.info(
            "まだ記録がありません。「メモ」画面の「食べたものメモ」から、"
            "作った料理を記録してみてください。"
        )
    else:
        st.metric("記録している料理の数（直近）", f"{len(logs)}件")
        log_df = pd.DataFrame(
            [{"日付": log.get("date", ""), "料理名": log.get("title", "")} for log in logs]
        )
        st.dataframe(log_df, use_container_width=True, hide_index=True)
except Exception as e:
    st.error("記録の読み込みに失敗しました。Firebaseの設定を確認してください。")
    st.exception(e)

st.divider()
st.caption("「スキャン」で食材を認識 →「栄養分析」「レシピ提案」で分析・提案 →「メモ」で買い物メモと記録、という流れで使えます。詳しい記録の傾向は「マイページ」でも確認できます。")
