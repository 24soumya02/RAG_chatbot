from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_llm

_SYSTEM = """You are a price comparison assistant. Extract price information from the search results and build a markdown comparison table.

Columns: Product | Platform/Store | Price | Link | Notes

Rules:
- Include only results where a price is visible in the snippet or title.
- Normalize prices (e.g. $999.99, US$89).
- Sort rows from cheapest to most expensive.
- The Link column must contain the raw URL.
- End with a 'Best pick:' recommendation line naming the cheapest reliable option."""


def _search(query, max_results=8):
    try:
        from ddgs import DDGS
    except ImportError:
        raise RuntimeError("web search unavailable: run 'pip install ddgs' to enable")

    with DDGS() as client:
        return list(client.text(f"{query} price", max_results=max_results))


def compare(question):
    results = _search(question)
    if not results:
        return f'No price results found for "{question}".'

    listings = "\n\n".join(
        f"Title: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}"
        for r in results
    )

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"Query: {question}\n\nSearch results:\n{listings}"),
    ]
    return get_llm().invoke(messages).content
