import streamlit as st
import pickle
import os
from datetime import datetime
from uuid import uuid4
import requests

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="GenAI Config Generator", page_icon="🧰", layout="wide")

st.markdown("""
    <style>
        .stChatMessage { margin-bottom: 1rem; }
        .user-bubble, .assistant-bubble {
            background: var(--primary-color);
            color: white;
            padding: 1rem;
            border-radius: 1rem;
            display: inline-block;
            max-width: 85%;
        }
        .edit-btn, .del-btn {
            cursor: pointer;
            font-size: 0.8rem;
            margin-left: 0.4rem;
            color: #999;
        }
        .edit-btn:hover, .del-btn:hover {
            color: #f33;
        }
        .sample-queries {
            margin-top: 2rem;
            font-style: italic;
            color: #aaa;
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
    chat_name = name if name else f"Config @ {timestamp}"
    conversations[chat_id] = {"name": chat_name, "messages": []}
    st.session_state.active_chat_id = chat_id
    save_conversations()

def save_conversations():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(conversations, f)

# Sidebar
with st.sidebar:
    st.title("🧰 GenAI Config Generator")
    new_chat_name = st.text_input("New Config Name", "")
    if st.button("➕ New Config"):
        create_new_chat(new_chat_name)
        st.rerun()

    st.markdown("---")
    st.subheader("Saved Configs")
    to_delete = None
    for cid, chat in conversations.items():
        cols = st.columns([8, 1, 1])
        with cols[0]:
            if st.button(f"{chat['name']}", key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.session_state.edit_index = None
                st.rerun()
        with cols[1]:
            st.markdown("<span class='edit-btn'>✏</span>", unsafe_allow_html=True)
        with cols[2]:
            if st.button("❌", key=f"del_{cid}"):
                to_delete = cid
    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.rerun()

# Chat Display
st.title("Generate Configuration")
chat_id = st.session_state.active_chat_id
if not chat_id:
    st.info("No configs yet. Try a sample input:")
    st.markdown("""
    <div class='sample-queries'>
        - Generate config for a 5G RAN node.
        - Create config with dynamic IP assignment.
        - Generate upgrade-ready template.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

messages = conversations[chat_id]["messages"]

for i, msg in enumerate(messages):
    col1, col2 = st.columns([12, 1])
    with col1:
        if msg["role"] == "user":
            if st.session_state.edit_index == i:
                new_text = st.text_area("Edit your input:", value=msg["content"], key=f"edit_{i}")
                if st.button("Update", key=f"resend_{i}"):
                    messages[i]["content"] = new_text
                    if i+1 < len(messages) and messages[i+1]["role"] == "assistant":
                        del messages[i+1]
                    requests.post("http://localhost:5002/query", json={"query": new_text})
                    messages.insert(i+1, {"role": "assistant", "content": "Response saved."})
                    st.session_state.edit_index = None
                    save_conversations()
                    st.rerun()
            else:
                st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("✏", key=f"editbtn_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        if st.button("🗑", key=f"delbtn_{i}"):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.rerun()

# User Input
user_input = st.text_area("Enter your config request:", key="main_input")
if st.button("Submit") and user_input.strip():
    messages.append({"role": "user", "content": user_input.strip()})
    requests.post("http://localhost:5002/query", json={"query": user_input.strip()})
    messages.append({"role": "assistant", "content": "Response saved."})
    save_conversations()
    st.rerun()


