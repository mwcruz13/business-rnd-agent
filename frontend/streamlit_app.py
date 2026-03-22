import os

import requests
import streamlit as st


BACKEND_API_BASE_URL = os.environ.get("BACKEND_API_BASE_URL", "http://localhost:8000")


st.set_page_config(page_title="BMI Consultant App", layout="wide")
st.title("BMI Consultant App")
st.caption("Scaffolded Streamlit frontend")

try:
    response = requests.get(f"{BACKEND_API_BASE_URL}/health", timeout=5)
    response.raise_for_status()
    st.success(f"Backend reachable: {response.json()}")
except Exception as exc:
    st.warning(f"Backend not reachable yet: {exc}")

uploaded = st.file_uploader("Upload a text or CSV input", type=["txt", "csv"])
if uploaded is not None:
    st.write({"name": uploaded.name, "type": uploaded.type, "size": uploaded.size})
