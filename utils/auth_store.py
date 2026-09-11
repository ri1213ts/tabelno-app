from utils.firebase_client import get_firestore_client


def load_credentials_from_firestore():
    """Firestoreに登録されている全ユーザーを、streamlit-authenticatorが読める形式で取得する"""
    db = get_firestore_client()
    docs = db.collection("auth_users").stream()

    usernames = {}
    for doc in docs:
        data = doc.to_dict()
        usernames[doc.id] = {
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "password": data.get("password", ""),
        }

    return {"usernames": usernames}


def save_user_to_firestore(username, user_data):
    """新規登録された1ユーザーの情報を、Firestoreに保存する"""
    db = get_firestore_client()
    db.collection("auth_users").document(username).set(
        {
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "password": user_data.get("password", ""),
        }
    )