
from app.services.call_llm import call_llm


def route(message: str) -> str:
    routing_prompt = f"""
You are a classifier that routes user queries.

Classify the query into ONE of the following categories:
- expense (questions about spending, money, totals, categories, transactions)
- document (questions about uploaded files, PDFs, reports, summaries)
- general (everything else)

Query: "{message}"

Respond with ONLY one word:
expense OR document or general
"""

    decision = call_llm(routing_prompt).strip().lower()

    for category in ["expense", "document", "general"]:
        if category in decision:
            return category

    return "document"
