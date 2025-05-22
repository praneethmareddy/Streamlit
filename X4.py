import streamlit as st
import requests
import pickle
import os
from datetime import datetime
from uuid import uuid4

DATA_FILE = "conversations.pkl"

st.set_page_config(page_title="Gradient Chatbot", page_icon="💬", layout="wide")

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
    st.title("💬 Chatbot")
    new_chat_name = st.text_input("New Chat Name", "")
    if st.button("➕ New Chat"):
        create_new_chat(new_chat_name)
        st.rerun()

    st.markdown("---")
    st.subheader("Conversations")
    to_delete = None
    for cid, chat in conversations.items():
        col1, col2 = st.columns([10, 2])
        with col1:
            if st.button(f"🗂 {chat['name']}", key=f"chat_{cid}"):
                st.session_state.active_chat_id = cid
                st.session_state.edit_index = None
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{cid}"):
                to_delete = cid
    if to_delete:
        del conversations[to_delete]
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
        save_conversations()
        st.rerun()

# Chat Display
st.title("Talk to Your Assistant")
chat_id = st.session_state.active_chat_id
if not chat_id:
    st.warning("Please create a new chat to begin.")
    st.markdown("### Try asking:")
    st.markdown("- What is the capital of France?")
    st.markdown("- Explain quantum physics simply")
    st.markdown("- Summarize the latest AI news")
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
                    st.rerun()
            else:
                st.chat_message("user", avatar="🧑‍💬").markdown(msg["content"])
        else:
            st.chat_message("assistant", avatar="🤖").markdown(msg["content"])

    with col2:
        if msg["role"] == "user":
            if st.button("✍️", key=f"editbtn_{i}", help="Edit"):
                st.session_state.edit_index = i
                st.rerun()
        if st.button("❌", key=f"delbtn_{i}", help="Delete"):
            del messages[i]
            if st.session_state.edit_index == i:
                st.session_state.edit_index = None
            save_conversations()
            st.rerun()

# User Input
st.markdown("<style>div[data-baseweb='textarea'] textarea { min-height: 100px; font-size: 18px; }</style>", unsafe_allow_html=True)
if prompt := st.chat_input("Type your message here..."):
    messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="🧑‍💬").markdown(prompt)

    try:
        res = requests.post("http://localhost:5002/query", json={"query": prompt})
        answer = res.json().get("response", "No response from server.")
    except Exception as e:
        answer = f"Error contacting server: {e}"

    messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant", avatar="🤖").markdown(answer)

    save_conversations()


Your updated Streamlit chatbot app now includes:

Light/dark mode with a consistent layout (no changing bubble colors)

Clean and compact icons for edit (✍️) and delete (❌)

Large message input box for better typing experience

Sample queries shown when no chats exist

Uses st.rerun() instead of deprecated experimental_rerun


Let me know if you'd like additional styling such as avatars, markdown/code highlighting, or persistent settings.

