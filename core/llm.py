import config
from langchain_openai import ChatOpenAI

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=config.MODEL_ID,
            api_key=config.HF_TOKEN,
            base_url=config.HF_BASE_URL,
            max_tokens=512,
            temperature=0.7,
            timeout=120,
        )
    return _llm