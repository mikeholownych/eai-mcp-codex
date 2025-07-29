
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import MarkdownTextSplitter
from qdrant_client import QdrantClient
import os
from langchain_community.vectorstores import Qdrant


CORPUS_DIR = "../secure-coding-corpus"

# Load documents
docs = []
for filename in os.listdir(CORPUS_DIR):
    if filename.endswith(".md"):
        loader = TextLoader(os.path.join(CORPUS_DIR, filename))
        docs.extend(loader.load())

# Split into chunks
splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# Embed and store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
qdrant = Qdrant.from_documents(
    chunks,
    embeddings,
    location="localhost",
    collection_name="secure_code_examples"
)
print(f"Embedded {len(chunks)} chunks.")
