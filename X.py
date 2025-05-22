import streamlit as st
import requests
import pickle
import os
from datetime import datetime

HISTORY_FILE = "chat_history.pkl"

st.set_page_config(page_title="Local Chatbot", page_icon="💬", layout="wide")

# Load chat history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "rb") as f:
        chat_history = pickle.load(f)
else:
    chat_history = []

# Sidebar
with st.sidebar:
    st.title("💬 Local Chatbot")
    if st.button("➕ New Chat"):
        chat_history = []
        with open(HISTORY_FILE, "wb") as f:
            pickle.dump(chat_history, f)
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Chat History")
    for i, msg in enumerate(chat_history):
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content'][:40]}...")

st.markdown("## Talk to your AI assistant")

# Chat display
for msg in chat_history:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    else:
        st.chat_message("assistant").markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask something..."):
    st.chat_message("user").markdown(prompt)
    chat_history.append({"role": "user", "content": prompt})

    # Send request
    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        answer = res.json().get("response", "No response from server.")
    except Exception as e:
        answer = f"Error contacting server: {e}"

    st.chat_message("assistant").markdown(answer)
    chat_history.append({"role": "assistant", "content": answer})

    with open(HISTORY_FILE, "wb") as f:
        pickle.dump(chat_history, f)
