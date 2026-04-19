"""
Runbook RAG - Retrieval-Augmented Generation over DevOps runbooks.
Uses LangChain + FAISS to index runbooks and retrieve relevant resolution steps.
"""

import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

RUNBOOKS_DIR = os.path.join(os.path.dirname(__file__), "runbooks")
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")


def load_and_index_runbooks() -> FAISS:
    """Load runbook markdown files and create a FAISS vector index."""
    loader = DirectoryLoader(
        RUNBOOKS_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} runbook documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"FAISS index saved to {FAISS_INDEX_PATH}")

    return vectorstore


def get_vectorstore() -> FAISS:
    """Load existing FAISS index or create a new one."""
    embeddings = OpenAIEmbeddings()
    if os.path.exists(FAISS_INDEX_PATH):
        print("Loading existing FAISS index...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        print("Creating new FAISS index from runbooks...")
        return load_and_index_runbooks()


def query_runbooks(query: str, vectorstore: FAISS = None) -> str:
    """Query the runbook knowledge base for relevant resolution steps."""
    if vectorstore is None:
        vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    results = []
    for i, doc in enumerate(docs, 1):
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        results.append(f"--- Runbook Match {i} (from {source}) ---\n{doc.page_content}")

    return "\n\n".join(results)


def query_runbooks_with_llm(query: str, vectorstore: FAISS = None) -> str:
    """Query runbooks with LLM-powered answer synthesis."""
    if vectorstore is None:
        vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(
        "Based on the following runbook context, answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Provide a clear, actionable answer with resolution steps."
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(query)
