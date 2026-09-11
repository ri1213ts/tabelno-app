from google import genai
import streamlit as st


def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
