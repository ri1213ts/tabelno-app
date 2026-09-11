import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from utils.auth_store import load_credentials_from_firestore, save_user_to_firestore

st.set_page_config(page_title="タベルノ", page_icon="🍳", layout="wide")

# ---- cookieの設定だけは、ローカルのconfig.yamlから読み込む ----
with open("config.yaml", encoding="utf-8") as file:
    app_config = yaml.load(file, Loader=SafeLoader)

# ---- ユーザーの認証情報は、Firestoreから読み込む ----
try:
    credentials = load_credentials_from_firestore()
except Exception as e:
    st.error("認証情報の読み込みに失敗しました。Firebaseの設定を確認してください。")
    st.exception(e)
    st.stop()

authenticator = stauth.Authenticate(
    credentials,
    app_config["cookie"]["name"],
    app_config["cookie"]["key"],
    app_config["cookie"]["expiry_days"],
)

auth_status = st.session_state.get("authentication_status")

# ---- ログインしていない場合：ログイン／新規登録タブを表示 ----
if auth_status is not True:
    st.title("🍳 タベルノ")
    st.caption("冷蔵庫の写真から、栄養管理と献立提案を。")

    login_tab, signup_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        authenticator.login()
        auth_status = st.session_state.get("authentication_status")
        if auth_status is False:
            st.error("ユーザー名またはパスワードが正しくありません")
        elif auth_status is None:
            st.info("ユーザー名とパスワードを入力してください（初めての方は「新規登録」タブへ）")

    with signup_tab:
        try:
            email, username, name = authenticator.register_user(captcha=False)
            if email:
                new_user_data = credentials["usernames"][username]
                save_user_to_firestore(username, new_user_data)
                st.success("登録が完了しました。「ログイン」タブからログインしてください。")
        except Exception as e:
            st.error(e)

    st.stop()

# ---- ここに来た時点でログイン成功 ----
with st.sidebar:
    st.write(f'ようこそ、**{st.session_state["name"]}** さん')
    authenticator.logout("ログアウト", "sidebar")
    st.divider()

pages = [
    st.Page("screens/home.py", title="ホーム", icon="🏠", default=True),
    st.Page("screens/scan.py", title="スキャン", icon="📷"),
    st.Page("screens/nutrition.py", title="栄養分析", icon="📊"),
    st.Page("screens/recipe.py", title="レシピ提案", icon="🍳"),
    st.Page("screens/shopping.py", title="メモ", icon="📝"),
    st.Page("screens/mypage.py", title="マイページ", icon="👤"),
]

pg = st.navigation(pages)
pg.run()