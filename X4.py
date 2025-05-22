import streamlit as st
import requests
import pickle
import os
from datetime import datetime
from uuid import uuid4

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="Gradient Chatbot", page_icon="🌟", layout="wide")

# Gradient UI and dark mode styling
st.markdown("""
    <style>
        body {
            background-color: #1e1e1e;
            color: white;
        }
        .stChatMessage { margin-bottom: 1rem; }
        .user-bubble {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1rem;
            border-radius: 1rem;
            display: inline-block;
            max-width: 85%;
        }
        .assistant-bubble {
            background: linear-gradient(135deg, #43cea2, #185a9d);
            color: white;
            padding: 1rem;
            border-radius: 1rem;
            display: inline-block;
            max-width: 85%;
        }
        .icon-btn {
            font-size: 0.85rem;
            padding: 2px 6px;
            margin-left: 4px;
            background: #444;
            color: white;
            border-radius: 6px;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        conversations = pickle.load(f)
else:
    conversations = {}

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Create new chat
def create_new_chat(name=None):
    chat_id = str(uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chat_name = name if name else f"Chat @ {timestamp}"
    conversations[chat_id] = {"name": chat_name, "messages": []}
    st.session_state.active_chat_id = chat_id
    save_conversations()

def save_conversations():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(conversations, f)

# Sidebar
with st.sidebar:
    st.title("🌟 Gradient Chatbot")
    new_chat_name = st.text_input("New Chat Name", "")
    if st.button("➕ New Chat"):
        create_new_chat(new_chat_name)
        st.rerun()

    st.markdown("---")
    st.subheader("Conversations")
    to_delete = None
    for cid, chat in conversations.items():
        col1, col2 = st.columns([10, 1])
        with col1:
            if st.button(f"📂 {chat['name']}", key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.session_state.edit_index = None
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{cid}"):
                to_delete = cid
    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.rerun()

# Main chat display
st.title("Talk to Your Assistant")
chat_id = st.session_state.active_chat_id

if not chat_id:
    st.info("No conversations found. Try one of these sample queries:")
    st.markdown("""
    - What is the capital of France?
    - Tell me a joke.
    - How does a black hole work?
    - Summarize the history of AI.
    """)
    st.stop()

messages = conversations[chat_id]["messages"]

# Display messages with small action icons
for i, msg in enumerate(messages):
    col1, col2 = st.columns([12, 1])
    with col1:
        if msg["role"] == "user":
            if st.session_state.edit_index == i:
                new_text = st.text_area("Edit your message:", value=msg["content"], key=f"edit_{i}")
                if st.button("Resend", key=f"resend_{i}"):
                    messages[i]["content"] = new_text
                    if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                        del messages[i + 1]
                    try:
                        res = requests.post("http://localhost:5002/query", json={"query": new_text})
                        answer = res.json().get("response", "No response from server.")
                    except Exception as e:
                        answer = f"Error: {e}"
                    messages.insert(i + 1, {"role": "assistant", "content": answer})
                    st.session_state.edit_index = None
                    save_conversations()
                    st.rerun()
            else:
                st.markdown(f'<div class="user-bubble">🧑‍💬 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("✏️", key=f"editbtn_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        if st.button("🗑️", key=f"delbtn_{i}"):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.rerun()

# Input box (larger)
prompt = st.chat_input("Ask something...")
if prompt:
    messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-bubble">🧑‍💬 {prompt}</div>', unsafe_allow_html=True)

    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        answer = res.json().get("response", "No response from server.")
    except Exception as e:
        answer = f"Error contacting server: {e}"

    messages.append({"role": "assistant", "content": answer})
    st.markdown(f'<div class="assistant-bubble">🤖 {answer}</div>', unsafe_allow_html=True)
    save_conversations()
