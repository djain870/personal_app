from rag import query_rag

def run(message):
    context = query_rag(message)

    return f"""
You are a document assistant.

Answer ONLY using this context:

{context}

Question:
{message}
"""