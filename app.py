import time

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import config
import core.price as price
from core.llm import get_llm

st.set_page_config(page_title="AI Assistant", layout="wide")

_CSS = """
<style>
.stApp {
    background: #f4f6f9;
}
[data-testid="stSidebar"] {
    background: #2c3e50;
}
[data-testid="stSidebar"] * {
    color: #ecf0f1;
}
[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #e3e7ed;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.footer {
    position: fixed;
    right: 20px;
    bottom: 10px;
    color: #2c3e50;
    font-size: 14px;
    background: #ffffff;
    border: 1px solid #e3e7ed;
    padding: 6px 14px;
    border-radius: 20px;
    z-index: 999;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
</style>
"""
st.markdown(_CSS, unsafe_allow_html=True)

_SYSTEM = SystemMessage(content="You are a helpful assistant.")

if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "current_id" not in st.session_state:
    st.session_state.current_id = None


def _new_id() -> str:
    return str(int(time.time() * 1000))


def _ensure_session():
    if st.session_state.current_id is None or st.session_state.current_id not in st.session_state.sessions:
        _start_session()


def _start_session() -> str:
    sid = _new_id()
    st.session_state.sessions[sid] = {"title": "New chat", "messages": []}
    st.session_state.current_id = sid
    return sid


def _current_messages():
    return st.session_state.sessions[st.session_state.current_id]["messages"]


def _to_messages():
    history = [_SYSTEM]
    for m in _current_messages():
        history.append(
            HumanMessage(content=m["content"])
            if m["role"] == "user"
            else AIMessage(content=m["content"])
        )
    return history


with st.sidebar:
    st.header("Plugins")
    price_mode = st.toggle(
        "Price comparison",
        help="When on, queries are answered with live web price comparisons.",
    )

    st.divider()

    st.header("Chats")
    if st.button("+ New chat", type="primary", use_container_width=True):
        _start_session()
        st.rerun()

    for sid, sess in reversed(list(st.session_state.sessions.items())):
        label = f"▶ {sess['title']}" if sid == st.session_state.current_id else sess["title"]
        if st.button(label, key=f"chat-{sid}", use_container_width=True):
            st.session_state.current_id = sid
            st.rerun()

    if st.session_state.sessions:
        if st.button("Clear all chats", type="primary", use_container_width=True):
            st.session_state.sessions = {}
            st.session_state.current_id = None
            st.rerun()

_ensure_session()

st.title("AI Assistant")
st.caption(
    f"Mode: {'Price comparison' if price_mode else 'Chat'} | Model: {config.MODEL_ID}"
    + ("" if config.HF_TOKEN else " (set HUGGINGFACEHUB_API_TOKEN in .env)")
)
st.markdown('<p class="footer">Developed by Soumya</p>', unsafe_allow_html=True)

messages = _current_messages()

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type a message..."):
    messages.append({"role": "user", "content": prompt})
    session = st.session_state.sessions[st.session_state.current_id]
    if session["title"] == "New chat":
        session["title"] = prompt if len(prompt) <= 40 else prompt[:40] + "..."

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        spinner = "Searching for prices..." if price_mode else "Thinking..."
        with st.spinner(spinner):
            try:
                if price_mode:
                    response = price.compare(prompt)
                else:
                    response = get_llm().invoke(_to_messages()).content
            except Exception as exc:
                response = f"Error: {exc}"
        st.markdown(response)
    messages.append({"role": "assistant", "content": response})