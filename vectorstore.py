import os
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import RAG_FILES_DIRS, VECTOR_STORE_PATH


def load_documents():
    """Carrega .txt e .pdf da pasta RAG; move ficheiros processados para processed/."""
    if not RAG_FILES_DIRS:
        return []

    os.makedirs(RAG_FILES_DIRS, exist_ok=True)
    processed_dir = os.path.join(RAG_FILES_DIRS, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    docs = []
    for name in os.listdir(RAG_FILES_DIRS):
        if name == "processed":
            continue
        path = os.path.join(RAG_FILES_DIRS, name)
        if not os.path.isfile(path):
            continue
        lower = name.lower()
        if not (lower.endswith(".txt") or lower.endswith(".pdf")):
            continue

        loader = (
            PyPDFLoader(path)
            if lower.endswith(".pdf")
            else TextLoader(path, encoding="utf-8")
        )
        docs.extend(loader.load())
        shutil.move(path, os.path.join(processed_dir, name))

    return docs


def get_vector_store():
    """Se houver documentos novos, indexa; senão reutiliza o Chroma em disco."""
    if not VECTOR_STORE_PATH:
        raise ValueError("VECTOR_STORE_PATH não definido")

    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

    embeddings = OpenAIEmbeddings()
    docs = load_documents()

    if docs:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        return Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=VECTOR_STORE_PATH,
        )

    return Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=embeddings,
    )
