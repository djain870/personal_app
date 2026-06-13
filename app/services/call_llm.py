from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint


load_dotenv()

_model = None


def get_model():
    global _model

    if _model is None:
        llm = HuggingFaceEndpoint(
            repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
            task="text-generation"
        )
        _model = ChatHuggingFace(llm=llm)

    return _model


def call_llm(prompt: str) -> str:
    model = get_model()
    result = model.invoke(prompt)
    return result.content
