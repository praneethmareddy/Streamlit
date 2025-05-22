import streamlit as st
import requests
import pickle
import os
from datetime import datetime
from uuid import uuid4

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="Gradient Chatbot", page_icon="🌟", layout="wide")

# Custom CSS for gradient theme
st.markdown("""
    <style>
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
        .edit-btn, .del-btn {
            cursor: pointer;
            font-size: 0.9rem;
            margin-left: 0.5rem;
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

# Create a new chat
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
        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Conversations")
    to_delete = None
    for cid, chat in conversations.items():
        if st.button(f"📂 {chat['name']}", key=f"chat_{cid}"):
            st.session_state.active_chat_id = cid
            st.session_state.edit_index = None
            st.experimental_rerun()
        if st.button("🔌 Delete", key=f"del_{cid}"):
            to_delete = cid
    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.experimental_rerun()

# Chat Display
st.title("Talk to Your Assistant")
chat_id = st.session_state.active_chat_id
if not chat_id:
    st.warning("Please create a new chat to begin.")
    st.stop()

messages = conversations[chat_id]["messages"]

for i, msg in enumerate(messages):
    col1, col2 = st.columns([12, 1])
    with col1:
        if msg["role"] == "user":
            if st.session_state.edit_index == i:
                new_text = st.text_area("Edit message:", value=msg["content"], key=f"edit_{i}")
                if st.button("Resend", key=f"resend_{i}"):
                    messages[i]["content"] = new_text
                    # Remove following assistant message (if exists)
                    if i+1 < len(messages) and messages[i+1]["role"] == "assistant":
                        del messages[i+1]
                    try:
                        res = requests.post("http://localhost:5002/query", json={"query": new_text})
                        answer = res.json().get("response", "No response from server.")
                    except Exception as e:
                        answer = f"Error: {e}"
                    messages.insert(i+1, {"role": "assistant", "content": answer})
                    st.session_state.edit_index = None
                    save_conversations()
                    st.experimental_rerun()
            else:
                st.markdown(f'<div class="user-bubble">🧑‍💬 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("✏️", key=f"editbtn_{i}"):
                st.session_state.edit_index = i
                st.experimental_rerun()
        if st.button("❌", key=f"delbtn_{i}"):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.experimental_rerun()

# User Input
if prompt := st.chat_input("Ask something..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧍"):
        st.markdown(prompt)

    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        answer = res.json().get("response", "No response from server.")
    except Exception as e:
        answer = f"Error contacting server: {e}"

    messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(answer)

    save_conversations()


