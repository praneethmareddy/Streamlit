import streamlit as st
import requests
import pickle
import os
from datetime import datetime
from uuid import uuid4

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="Gradient Chatbot", page_icon="🌟", layout="wide")

# Force dark mode via custom CSS
st.markdown("""
    <style>
        html, body, [class*="css"] {
            background-color: #121212 !important;
            color: #e0e0e0 !important;
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
            font-size: 0.8rem;
            padding: 0.2rem;
        }
        .sample-query {
            background: #2c2c2c;
            padding: 0.6rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            display: inline-block;
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
        st.rerun()

    st.markdown("---")
    st.subheader("Conversations")
    to_delete = None
    for cid, chat in conversations.items():
        cols = st.columns([8, 1, 1])
        with cols[0]:
            if st.button(f"📂 {chat['name']}", key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.session_state.edit_index = None
                st.rerun()
        with cols[1]:
            if st.button("🖉", key=f"edit_chat_{cid}", help="Rename"):
                new_name = st.text_input("Rename Chat", value=chat["name"], key=f"name_{cid}")
                if new_name:
                    chat["name"] = new_name
                    save_conversations()
                    st.rerun()
        with cols[2]:
            if st.button("🗑️", key=f"del_{cid}", help="Delete"):
                to_delete = cid
    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.rerun()

# Main Chat UI
st.title("Talk to Your Assistant")
chat_id = st.session_state.active_chat_id

if not chat_id:
    st.info("No conversations yet. Try a sample query below!")
    sample_queries = [
        "What is Streamlit?",
        "Give me a summary of today's news.",
        "Explain the difference between AI and ML.",
        "How do I deploy a FastAPI app?",
        "Tell me a fun fact!"
    ]
    for q in sample_queries:
        if st.button(q, key=q):
            create_new_chat()
            st.session_state.active_chat_id = list(conversations.keys())[-1]
            conversations[st.session_state.active_chat_id]["messages"].append({"role": "user", "content": q})
            try:
                res = requests.post("http://localhost:5002/query", json={"query": q})
                answer = res.json().get("response", "No response from server.")
            except Exception as e:
                answer = f"Error: {e}"
            conversations[st.session_state.active_chat_id]["messages"].append({"role": "assistant", "content": answer})
            save_conversations()
            st.rerun()
    st.stop()

messages = conversations[chat_id]["messages"]

for i, msg in enumerate(messages):
    col1, col2 = st.columns([12, 1])
    with col1:
        if msg["role"] == "user":
            if st.session_state.edit_index == i:
                new_text = st.text_area("Edit message:", value=msg["content"], key=f"edit_{i}")
                if st.button("🔄 Resend", key=f"resend_{i}"):
                    messages[i]["content"] = new_text
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
                    st.rerun()
            else:
                st.markdown(f'<div class="user-bubble">🧑‍💬 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    with col2:
        if msg["role"] == "user":
            if st.button("🖉", key=f"editbtn_{i}", help="Edit", use_container_width=True):
                st.session_state.edit_index = i
                st.rerun()
        if st.button("🗑️", key=f"delbtn_{i}", help="Delete", use_container_width=True):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.rerun()

# Input Box
if prompt := st.chat_input("Ask something..."):
    messages.append({"role": "user", "content": prompt})
    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        answer = res.json().get("response", "No response from server.")
    except Exception as e:
        answer = f"Error contacting server: {e}"
    messages.append({"role": "assistant", "content": answer})
    save_conversations()
    st.rerun()
