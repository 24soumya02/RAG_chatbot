# 🧠 RAG Chatbot — Streamlit + Weaviate + LangGraph

An interactive **RAG (Retrieval-Augmented Generation)** chatbot built with **Streamlit**, **Weaviate**, and **LangChain/LangGraph**.  
This chatbot retrieves relevant documents from a **Weaviate vector database**, constructs a **context-aware prompt**, and invokes a **language model** to generate accurate, grounded responses.  

---

## 🚀 Features

- 🔍 **Semantic Search with Weaviate:** Finds the top 10 most relevant documents for each user query.  
- 🧩 **Context Injection:** Merges retrieved content with the user’s query before passing to the model.  
- 🤖 **LLM Response Generation:** Uses an LLM (e.g., OpenAI, Anthropic, or other) for conversational replies.  
- 💬 **Streaming Responses:** Real-time token streaming via `st.write_stream()`.  
- 💾 **Session History:** Maintains chat context using Streamlit session state.  
- ⚙️ **Thread Management:** Supports conversation threads using `thread_id`.  

---

## 🧱 Architecture

```
User Input → Weaviate Search (Top 10) → Prompt Builder (Context + Query)
→ LLM Invocation (LangGraph) → Streamed Response → Display in Streamlit
```

---

## 📄 Example Code

```python
import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
from weaviate import Client

st.title("RAG Chatbot — Streamlit + Weaviate")
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

# Initialize chat history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Display existing messages
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Get user input
user_input = st.chat_input("Type your question here...")

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):

        # --- Step 1: Search Weaviate ---
        client = Client("https://your-weaviate-endpoint")
        results = client.query.get("Document", ["content"]).with_near_text({"concepts": [user_input]}).with_limit(10).do()
        context = "\n\n".join([item["content"] for item in results["data"]["Get"]["Document"]])

        # --- Step 2: Build Prompt ---
        prompt = f"Context:\n{context}\n\nUser Query:\n{user_input}"

        # --- Step 3: Stream Model Response ---
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=prompt)]},
                config=CONFIG,
                stream_mode="messages"
            )
        )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
```

---

## 🧰 Requirements

```bash
pip install streamlit weaviate-client langchain-core langgraph openai
```

---

## ⚙️ Environment Variables

Create a `.env` file with the following:
```
OPENAI_API_KEY=your_api_key_here
WEAVIATE_URL=https://your-weaviate-instance
```

Load them in your app (optional):
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🧪 Run the App

```bash
streamlit run app.py
```

Then open in your browser at:  
👉 http://localhost:8501  

---

## 🧠 Future Enhancements

- Add **source citations** for retrieved content  
- Implement **conversation summarization**  
- Support **multiple vector DBs** (FAISS, Chroma, Pinecone)  
- Add **user authentication**
