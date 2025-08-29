
import streamlit as st
from utils import ask_backend

st.set_page_config(page_title="Kaspa Gemini Chatbot", page_icon="💬", layout="wide")

# --- Sidebar ---
st.markdown("""
    <style>
    .block-container {padding-top: 2rem;}
    .css-1d391kg {background: #eaf1fb;}
    .sidebar-content {background: #f6f8fc; border-radius: 18px; padding: 1.5rem 1rem;}
    .sidebar-title {font-weight: bold; font-size: 1.2rem; margin-bottom: 1.2rem;}
    .chat-history-item {display: flex; align-items: center; gap: 0.7rem; padding: 0.5rem 0.7rem; border-radius: 10px; margin-bottom: 0.5rem; cursor: pointer; transition: background 0.2s;}
    .chat-history-item:hover {background: #e0e7ef;}
    .chat-history-icon {font-size: 1.1rem;}
    .new-chat-btn {background: #3b82f6; color: white; border: none; border-radius: 20px; padding: 0.6rem 1.2rem; font-weight: 600; margin-bottom: 1.5rem; cursor: pointer;}
    .new-chat-btn:hover {background: #2563eb;}
    .dark-mode-btn {margin-top: 2rem; color: #64748b; font-size: 1rem;}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<button class="new-chat-btn">+ New Chat</button>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Chat history</div>', unsafe_allow_html=True)
    chat_histories = [
        ("🟣", "Gemini help request"),
        ("🔵", "AI vs Developers"),
        ("🟢", "Math puzzle solution"),
        ("🟠", "Vibe coding experience")
    ]
    for icon, label in chat_histories:
        st.markdown(f'<div class="chat-history-item"><span class="chat-history-icon">{icon}</span> {label}</div>', unsafe_allow_html=True)
    st.markdown('<div class="dark-mode-btn">🌙 Dark mode</div>', unsafe_allow_html=True)

# --- Main Chat Area ---
st.markdown("""
    <style>
    .chat-header {font-size: 2.1rem; font-weight: 700; color: #3b82f6; margin-bottom: 1.5rem; text-align: center;}
    .chat-bubble {padding: 1.1rem 1.3rem; border-radius: 16px; margin-bottom: 1.1rem; max-width: 70%; font-size: 1.08rem;}
    .chat-bubble.user {background: #e5eaf1; color: #222; margin-left: auto; text-align: right;}
    .chat-bubble.bot {background: #f6f8fc; color: #222; margin-right: auto; text-align: left; box-shadow: 0 2px 8px #e0e7ef;}
    .chat-bubble .star {color: #3b82f6; font-size: 1.2rem; margin-right: 0.5rem;}
    .chat-input-row {display: flex; align-items: center; background: #f6f8fc; border-radius: 30px; padding: 0.5rem 1.2rem; margin-top: 1.5rem;}
    .chat-input {flex: 1; border: none; background: transparent; font-size: 1.1rem; padding: 0.7rem 0; outline: none;}
    .send-btn {background: #3b82f6; color: white; border: none; border-radius: 50%; width: 2.5rem; height: 2.5rem; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-left: 0.7rem; cursor: pointer;}
    .send-btn:hover {background: #2563eb;}
    .copy-btn {background: #e0e7ef; color: #3b82f6; border: none; border-radius: 8px; padding: 0.2rem 0.7rem; font-size: 0.95rem; margin-top: 0.5rem; cursor: pointer;}
    .copy-btn:hover {background: #d1e0f7;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-header">Gemini Chatbot in React JS & CSS <span style="font-size:1.5rem;vertical-align:middle;">⚛️</span> <span style="font-size:1.5rem;vertical-align:middle;">🛡️</span></div>', unsafe_allow_html=True)


# --- Chat State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "bot", "content": "Hi there! I'm Gemini. How can I assist you today?", "star": True}
    ]

# --- Chat Display ---
for msg in st.session_state.chat_history:
    if msg["role"] == "bot":
        st.markdown(f'<div class="chat-bubble bot">' + ("<span class='star'>★</span> " if msg.get("star") else "") + msg["content"] + '</div>', unsafe_allow_html=True)
        # Show citations if present
        if msg.get("citations"):
            for c in msg["citations"]:
                st.markdown(f'<div style="font-size:0.95rem;color:#64748b;margin-left:1.5rem;">📎 <b>{c.get("filename") or c.get("source")}</b> {c.get("section", "")} <a href="{c.get("url", "")}" target="_blank">{c.get("url", "")}</a></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble user">{msg["content"]}</div>', unsafe_allow_html=True)

# --- Chat Input ---
col1, col2 = st.columns([8,1])
with col1:
    user_input = st.text_input("", "", key="chat_input", placeholder="Message Gemini...", label_visibility="collapsed")
with col2:
    send_clicked = st.button("⬆️", key="send_btn", help="Send", use_container_width=True)

# --- Handle Sending ---
if (user_input and (send_clicked or (st.session_state.get("last_input") != user_input))):
    st.session_state.last_input = user_input
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.spinner("Gemini is thinking..."):
        answer, citations = ask_backend(user_input)
    st.session_state.chat_history.append({"role": "bot", "content": answer, "citations": citations, "star": True if citations else False})
    st.experimental_rerun()
