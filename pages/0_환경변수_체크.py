import streamlit as st
from utils.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL_SCHEDULE,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
)

st.title("환경 변수 체크")

st.write("OPENAI_API_KEY 존재 여부:", bool(OPENAI_API_KEY))
st.write("OPENAI_MODEL_SCHEDULE:", OPENAI_MODEL_SCHEDULE)

st.write("GOOGLE—CLIENT_ID 존재 여부:", bool(GOOGLE_API_KEY))
st.write("GOOGLE_CLIENT_SECRET 존재 여부:", bool(GOOGLE_CSE_ID))

st.write("GOOGLE_CLIENT_ID 실제 값 (앞 5글자만):", repr((GOOGLE_API_KEY or "")[:5]))
st.write("GOOGLE_CLIENT_SECRET 실제 값 (앞 5글자만):", repr((GOOGLE_CSE_ID or "")[:5]))
