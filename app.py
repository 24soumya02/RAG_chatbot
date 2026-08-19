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


def _to_messages():
    history = [_SYSTEM]
    for m in st.session_state.messages:
        history.append(
            HumanMessage(content=m["content"])
            if m["role"] == "user"
            else AIMessage(content=m["content"])
        )
    return history


with st.sidebar:
    st.header("Chat History")
    for m in st.session_state.get("messages", [])[-10:]:
        content = m["content"] if len(m["content"]) <= 150 else m["content"][:150] + "..."
        with st.container(border=True):
            st.caption("You" if m["role"] == "user" else "Assistant")
            st.markdown(content, unsafe_allow_html=False)
    if st.session_state.get("messages"):
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.divider()
    st.header("Plugins")
    price_mode = st.toggle(
        "Price comparison",
        help="When on, queries are answered with live web price comparisons.",
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI Assistant")
st.caption(
    f"Mode: {'Price comparison' if price_mode else 'Chat'} | Model: {config.MODEL_ID}"
    + ("" if config.HF_TOKEN else " (set HUGGINGFACEHUB_API_TOKEN in .env)")
)
st.markdown('<p class="footer">Developed by Soumya</p>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
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
    st.session_state.messages.append({"role": "assistant", "content": response})