
from langchain.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI  # Replace with your local LLM if needed

# Connect to Qdrant
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Qdrant(
    collection_name="secure_code_examples",
    embeddings=embeddings,
    location="localhost"
)

retriever = db.as_retriever()

# Retrieval-based QA
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    retriever=retriever,
    return_source_documents=True
)

def answer_query(query):
    result = qa_chain.run(query)
    return result
