import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st


def get_firestore_client():
    """Firestoreクライアントを取得する（アプリ内で使い回す）"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def save_meal_log(username, title, date_str, nutrition_totals=None):
    """「何を食べたか」の記録を1件、Firestoreに保存する。
    nutrition_totals を渡すと、その料理のカロリー・栄養素も一緒に記録される。
    """
    db = get_firestore_client()
    data = {
        "title": title,
        "date": date_str,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    if nutrition_totals:
        data["nutrition"] = {k: round(v, 1) for k, v in nutrition_totals.items()}

    db.collection("users").document(username).collection("meal_logs").add(data)


def get_meal_logs(username, limit=10):
    """直近の「食べたもの」記録を、新しい順に取得する"""
    db = get_firestore_client()
    docs = (
        db.collection("users")
        .document(username)
        .collection("meal_logs")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


def get_all_meal_logs(username):
    """「食べたもの」記録を全件取得する（マイページの集計用）"""
    db = get_firestore_client()
    docs = (
        db.collection("users")
        .document(username)
        .collection("meal_logs")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [doc.to_dict() for doc in docs]