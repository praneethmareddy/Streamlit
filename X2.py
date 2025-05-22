import streamlit as st import requests import pickle import os from datetime import datetime from uuid import uuid4

DATA_FILE = "conversations.pkl"

---------- Persistent Storage ----------

if os.path.exists(DATA_FILE): with open(DATA_FILE, "rb") as f: conversations = pickle.load(f) else: conversations = {}

---------- Session State ----------

if "active_chat_id" not in st.session_state: st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None if "edit_index" not in st.session_state: st.session_state.edit_index = None if "edit_text" not in st.session_state: st.session_state.edit_text = ""

---------- Helpers ----------

def save_conversations(): with open(DATA_FILE, "wb") as f: pickle.dump(conversations, f)

def create_new_chat(name=None): cid = str(uuid4()) title = name if name else f"Chat @ {datetime.now().strftime('%Y-%m-%d %H:%M')}" conversations[cid] = {"name": title, "messages": []} st.session_state.active_chat_id = cid save_conversations()

---------- Sidebar ----------

with st.sidebar: st.title("💬 Local Chatbot")

new_chat_name = st.text_input("New Chat Name")
if st.button("➕ New Chat"):
    create_new_chat(new_chat_name if new_chat_name else None)
    st.experimental_rerun()

st.markdown("---")
st.subheader("Conversations")
to_delete = None
for cid, chat in conversations.items():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        if st.button(chat['name'], key=f"select_{cid}"):
            st.session_state.active_chat_id = cid
            st.experimental_rerun()
    with col2:
        if st.button("🗑️", key=f"del_{cid}"):
            to_delete = cid

if to_delete:
    del conversations[to_delete]
    if st.session_state.active_chat_id == to_delete:
        st.session_state.active_chat_id = list(conversations.keys())[0] if conversations else None
    save_conversations()
    st.experimental_rerun()

---------- Main UI ----------

st.markdown(""" <style> .message-container {margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 12px; background: linear-gradient(145deg, #e0e0e0, #ffffff);} .assistant {background: linear-gradient(145deg, #d1f0ff, #f0f9ff);} .user {background: linear-gradient(145deg, #fce4ec, #f8bbd0);} .icon {font-size: 1.4rem; margin-right: 0.5rem;} </style> """, unsafe_allow_html=True)

if not st.session_state.active_chat_id: st.info("Start a new chat to begin.") st.stop()

chat = conversations[st.session_state.active_chat_id]

---------- Display Chat Messages ----------

for idx, msg in enumerate(chat["messages"]): col1, col2 = st.columns([0.9, 0.1]) with col1: st.markdown(f"<div class='message-container {msg['role']}'>", unsafe_allow_html=True) icon = "🧑" if msg['role'] == "user" else "🤖" st.markdown(f"<span class='icon'>{icon}</span>", unsafe_allow_html=True)

if st.session_state.edit_index == idx:
        new_text = st.text_area("Edit your message:", value=st.session_state.edit_text, key=f"edit_input_{idx}")
        if st.button("Resend", key=f"resend_{idx}"):
            chat['messages'][idx]['content'] = new_text
            # Delete the assistant's old response
            if idx+1 < len(chat['messages']) and chat['messages'][idx+1]['role'] == 'assistant':
                del chat['messages'][idx+1]
            try:
                res = requests.post("http://localhost:5002/query", json={"query": new_text})
                answer = res.json().get("response", "No response from server.")
            except Exception as e:
                answer = f"Error: {e}"
            chat['messages'].insert(idx+1, {"role": "assistant", "content": answer})
            st.session_state.edit_index = None
            save_conversations()
            st.experimental_rerun()
    else:
        st.markdown(msg["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    if msg['role'] == 'user':
        if st.button("✏️", key=f"edit_{idx}"):
            st.session_state.edit_index = idx
            st.session_state.edit_text = msg['content']
            st.experimental_rerun()
    if st.button("❌", key=f"delete_{idx}"):
        del chat['messages'][idx]
        save_conversations()
        st.experimental_rerun()

---------- Chat Input ----------

prompt = st.chat_input("Ask something...") if prompt: chat['messages'].append({"role": "user", "content": prompt}) with st.chat_message("user", avatar="🧑"): st.markdown(prompt)

try:
    res = requests.post("http://localhost:5002/query", json={"query": prompt})
    answer = res.json().get("response", "No response from server.")
except Exception as e:
    answer = f"Error: {e}"

chat['messages'].append({"role": "assistant", "content": answer})
with st.chat_message("assistant", avatar="🤖"):
    st.markdown(answer)

save_conversations()

