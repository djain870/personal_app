from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
import os


# embedding model
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# persistent vector DB
DB_DIR = "vector_db"

def process_document(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    vectordb = Chroma.from_documents(
        chunks,
        embedding,
        persist_directory=DB_DIR
    )
    # Chroma now auto-persists, no need to call persist()


def query_rag(question):
    vectordb = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding
    )

    docs = vectordb.similarity_search(question, k=3)

    context = "\n\n".join([doc.page_content for doc in docs])

    return context