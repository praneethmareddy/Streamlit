import streamlit as st
import requests
import pickle
import os
import json
from uuid import uuid4

HISTORY_FILE = "chat_history.pkl"
SAMPLE_QUERIES = [
    "What is the capital of France?",
    "Explain the theory of relativity in simple terms.",
    "How can I improve my productivity?",
    "Tell me a fun programming fact.",
    "What’s the weather like in Tokyo today?"
]

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")

# Inject gradient CSS
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
.chat-container {
    margin: 20px 0;
}
.user-msg, .ai-msg {
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    max-width: 80%;
}
.user-msg {
    background: linear-gradient(135deg, #3e8ed0, #6eaddf);
    color: white;
    align-self: flex-end;
}
.ai-msg {
    background: linear-gradient(135deg, #2c5364, #203a43);
    color: white;
    align-self: flex-start;
}
.edit-button {
    font-size: 12px;
    margin-left: 10px;
}
</style>
""", unsafe_allow_html=True)

# Load or initialize chat history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "rb") as f:
        chat_history = pickle.load(f)
else:
    chat_history = []

# Sidebar
with st.sidebar:
    st.title("💬 AI Chatbot")
    theme = st.radio("Theme", ["Dark", "Light"], horizontal=True)
    if theme == "Light":
        st.markdown("<style>body { background: #f7f7f7 !important; color: black !important; }</style>", unsafe_allow_html=True)

    if st.button("➕ New Chat"):
        chat_history = []
        with open(HISTORY_FILE, "wb") as f:
            pickle.dump(chat_history, f)
        st.experimental_rerun()

    if st.button("📤 Export Chat"):
        st.download_button(
            label="Download as JSON",
            data=json.dumps(chat_history, indent=2),
            file_name="chat_history.json",
            mime="application/json"
        )

    st.markdown("---")
    st.subheader("Sample Queries")
    for q in SAMPLE_QUERIES:
        if st.button(q):
            st.session_state["prompt"] = q
            st.experimental_rerun()

# Show conversation
st.title("🌟 Chat with Your AI Assistant")

delete_index = None
edit_index = None
edited_text = ""

for idx, msg in enumerate(chat_history):
    col1, col2 = st.columns([9, 1])
    with col1:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">🧑‍💻 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-msg">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("✏️", key=f"edit_{idx}"):
                edit_index = idx
                edited_text = msg["content"]
        if st.button("🗑️", key=f"delete_{idx}"):
            delete_index = idx

# Handle edit
if edit_index is not None:
    new_text = st.text_input("Edit your question:", value=edited_text)
    if st.button("Submit Edit"):
        chat_history[edit_index]["content"] = new_text
        chat_history = chat_history[:edit_index+1]  # delete following responses
        with open(HISTORY_FILE, "wb") as f:
            pickle.dump(chat_history, f)
        st.success("Edited! Please re-submit to regenerate response.")
        st.experimental_rerun()

# Handle delete
if delete_index is not None:
    del chat_history[delete_index]
    with open(HISTORY_FILE, "wb") as f:
        pickle.dump(chat_history, f)
    st.experimental_rerun()

# User input
prompt = st.chat_input("Ask something...") or st.session_state.pop("prompt", "")

if prompt:
    st.markdown(f'<div class="user-msg">🧑‍💻 {prompt}</div>', unsafe_allow_html=True)
    chat_history.append({"role": "user", "content": prompt})

    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        response = res.json().get("response", "No response from server.")
    except Exception as e:
        response = f"Error: {e}"

    st.markdown(f'<div class="ai-msg">🤖 {response}</div>', unsafe_allow_html=True)
    chat_history.append({"role": "assistant", "content": response})

    with open(HISTORY_FILE, "wb") as f:
        pickle.dump(chat_history, f)
