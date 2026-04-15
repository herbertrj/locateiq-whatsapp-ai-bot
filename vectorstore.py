import logging
import os
import shutil

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config import RAG_FILES_DIR, VECTOR_STORE_PATH

logger = logging.getLogger(__name__)


def _non_empty_docs(docs: list[Document]) -> list[Document]:
    return [d for d in docs if (d.page_content or "").strip()]


def _reset_chroma_persist_dir(path: str | None) -> None:
    """
    Chroma reutiliza a pasta em disco: sem apagar, novos PDFs misturam-se com
    embeddings antigos (ex.: Ultra IPTV) e o RAG continua a devolver trechos velhos.
    """
    if not path:
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def load_documents() -> list[Document]:
    docs: list[Document] = []
    if not RAG_FILES_DIR or not os.path.isdir(RAG_FILES_DIR):
        return docs

    processed_dir = os.path.join(RAG_FILES_DIR, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    files = [
        os.path.join(RAG_FILES_DIR, f)
        for f in os.listdir(RAG_FILES_DIR)
        if f.endswith(".pdf") or f.endswith(".txt")
    ]

    for file in files:
        if not os.path.isfile(file):
            continue
        try:
            loader = PyPDFLoader(file) if file.endswith(".pdf") else TextLoader(file, encoding="utf-8")
            batch = _non_empty_docs(loader.load())
        except Exception as exc:
            logger.exception("Falha ao ler %s: %s", file, exc)
            continue

        if not batch:
            logger.warning(
                "Nenhum texto extraível de %s; ficheiro não movido para processed.",
                file,
            )
            continue

        docs.extend(batch)
        dest_path = os.path.join(processed_dir, os.path.basename(file))
        shutil.move(file, dest_path)

    return docs


def get_vectorstore():
    docs = load_documents()
    embeddings = OpenAIEmbeddings()

    if not docs:
        return Chroma(
            embedding_function=embeddings,
            persist_directory=VECTOR_STORE_PATH,
        )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splits = [s for s in text_splitter.split_documents(docs) if (s.page_content or "").strip()]
    if not splits:
        logger.warning("Splits vazios; a abrir vectorstore existente.")
        return Chroma(
            embedding_function=embeddings,
            persist_directory=VECTOR_STORE_PATH,
        )

    _reset_chroma_persist_dir(VECTOR_STORE_PATH)

    return Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_PATH,
    )