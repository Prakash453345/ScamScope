import os

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma



# Path where your scam documents are stored
DATA_PATH = "data/scam_docs"

# Path where vector database will be stored
DB_PATH = "vector_db"


def ingest_documents():
    documents = []

    # Load all .txt files from scam_docs
    for file in os.listdir(DATA_PATH):
        if file.endswith(".txt"):
            file_path = os.path.join(DATA_PATH, file)
            loader = TextLoader(file_path, encoding="utf-8")
            documents.extend(loader.load())

    # Split documents into semantic chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Store embeddings in ChromaDB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    print("✅ Scam knowledge base built successfully.")

if __name__ == "__main__":
    ingest_documents()