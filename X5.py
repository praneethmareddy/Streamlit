import streamlit as st
import requests
import pickle
import os
from datetime import datetime
from uuid import uuid4

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="Gradient Chatbot", page_icon="🌟", layout="wide")

# Apply dark mode
st.markdown("""
    <style>
        html, body, [class*="st-"] {
            background-color: #1e1e1e;
            color: white;
        }
        .chat-bubble {
            background-color: #333333;
            padding: 1rem;
            border-radius: 0.75rem;
            margin-bottom: 0.5rem;
            display: inline-block;
            max-width: 85%;
        }
        .chat-avatar {
            margin-right: 0.5rem;
        }
        .icon-button {
            font-size: 0.75rem !important;
            padding: 0.2rem 0.4rem !important;
            margin-left: 0.2rem;
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

# Functions
def save_conversations():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(conversations, f)

def create_new_chat(name=None):
    chat_id = str(uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chat_name = name if name else f"Chat @ {timestamp}"
    conversations[chat_id] = {"name": chat_name, "messages": []}
    st.session_state.active_chat_id = chat_id
    save_conversations()

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
        col1, col2 = st.columns([8, 2])
        with col1:
            if st.button(chat["name"], key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.session_state.edit_index = None
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{cid}", help="Delete"):
                to_delete = cid

    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.rerun()

# Chat display
st.title("Talk to Your Assistant")

chat_id = st.session_state.active_chat_id
if not chat_id:
    st.warning("Please create a new chat to begin.")
    st.markdown("#### Sample Queries:")
    st.markdown("- What's the weather like today?")
    st.markdown("- Summarize the latest AI news.")
    st.markdown("- Explain reinforcement learning.")
    st.markdown("- Generate a poem about the moon.")
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

                    # Update chat name if it's the first message
                    if i == 0:
                        conversations[chat_id]["name"] = new_text[:30] + "..." if len(new_text) > 30 else new_text

                    # Remove assistant message after it
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
                st.markdown(f'<div class="chat-bubble"><strong>🧑‍💬</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble"><strong>🤖</strong> {msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("✏️", key=f"editbtn_{i}", help="Edit", use_container_width=True):
                st.session_state.edit_index = i
                st.rerun()
        if st.button("🗑️", key=f"delbtn_{i}", help="Delete", use_container_width=True):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.rerun()

# Chat Input
if prompt := st.chat_input("Ask something..."):
    messages.append({"role": "user", "content": prompt})
    if len(messages) == 1:
        conversations[chat_id]["name"] = prompt[:30] + "..." if len(prompt) > 30 else prompt

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
