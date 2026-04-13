
from typing import Any


def route(client: Any, message: str) -> str:
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

    result = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=[{"role": "user", "content": routing_prompt}]
    )

    decision = result.choices[0].message.content.strip().lower()

    # Fallback safety
    if decision not in ["expense", "document", "general"]:
        return "document"

    return decision