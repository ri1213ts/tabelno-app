import json
import pandas as pd
import streamlit as st
from google.genai import types
from utils.gemini_client import get_gemini_client

st.title("📷 スキャン")
st.write("冷蔵庫の写真を撮影するか、アップロードしてください。")

if "ingredients" not in st.session_state:
    st.session_state.ingredients = []

input_method = st.radio("入力方法を選んでください", ["カメラで撮影", "写真をアップロード"])

photo = None
if input_method == "カメラで撮影":
    photo = st.camera_input("冷蔵庫を撮影してください")
else:
    photo = st.file_uploader("写真を選択してください", type=["jpg", "jpeg", "png"])

if photo is not None:
    st.image(photo, caption="アップロードされた写真", use_container_width=True)

    if st.button("この写真から食材を認識する"):
        with st.spinner("AIが写真を確認しています..."):
            try:
                client = get_gemini_client()

                response_schema = {
                    "type": "object",
                    "properties": {
                        "ingredients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "quantity": {"type": "string"},
                                },
                                "required": ["name", "quantity"],
                            },
                        }
                    },
                    "required": ["ingredients"],
                }

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=[
                        "写真に写っている食材をすべて日本語でリストアップしてください。それぞれの推定量も簡潔に記載してください。",
                        types.Part.from_bytes(data=photo.getvalue(), mime_type=photo.type),
                    ],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": response_schema,
                    },
                )

                result = json.loads(response.text)
                st.session_state.ingredients = result["ingredients"]
                st.success("食材を認識しました。下で確認・修正してください。")

            except json.JSONDecodeError:
                st.error("AIの応答をうまく読み取れませんでした。もう一度お試しください。")
            except Exception as e:
                st.error("食材の認識中にエラーが発生しました。通信状況を確認し、もう一度お試しください。")
                st.exception(e)

st.divider()
st.subheader("認識された食材（自由に編集できます）")

if st.session_state.ingredients:
    df = pd.DataFrame(st.session_state.ingredients)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    st.session_state.ingredients = edited_df.to_dict("records")
else:
    st.write("まだ食材が認識されていません。上のボタンで写真から認識してください。")
