"""
rag/document_rag.py - Document RAG Pipeline
=============================================
Handles:
  1. Ingesting PDF / TXT files
  2. Splitting text into chunks
  3. Creating embeddings and storing in FAISS
  4. Answering questions using retrieved chunks
"""

import os
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import tempfile

# ── Use our central config — no .env, no os.getenv ───────────────────────────
from config import create_llm, create_embeddings


class DocumentRAG:
    """
    RAG pipeline for uploaded documents (PDF and TXT).
    Uses HuggingFace embeddings (local, free) + OpenRouter LLM.
    """

    def __init__(self):
        # HuggingFace embeddings — runs locally, no API key needed
        self.embeddings = create_embeddings()

        # OpenRouter LLM via our factory
        self.llm = create_llm(temperature=0.3)

        # Text splitter - breaks documents into chunks
        # chunk_size=500: each chunk ~500 characters
        # chunk_overlap=50: chunks share 50 chars with neighbor (for context continuity)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        # Vector store - will be set after first document upload
        self.vector_store = None
        self.retrieval_chain = None

    def ingest(self, file_bytes: bytes, filename: str) -> str:
        """
        Process an uploaded document:
          1. Save to temp file
          2. Load and parse
          3. Split into chunks
          4. Create embeddings
          5. Store in FAISS
        """
        # Save file to a temp location so LangChain loaders can read it
        suffix = ".pdf" if filename.endswith(".pdf") else ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Load the document using the appropriate loader
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(tmp_path)
            else:
                loader = TextLoader(tmp_path, encoding="utf-8")

            documents = loader.load()

            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            print(f"[DocumentRAG] Loaded {len(documents)} pages → {len(chunks)} chunks")

            # Create or update the vector store
            if self.vector_store is None:
                # First document: create a new FAISS index
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                # Additional documents: add to existing index
                self.vector_store.add_documents(chunks)

            # Build the retrieval chain
            self._build_chain()

            return f"✅ Successfully processed '{filename}' ({len(chunks)} chunks indexed)"

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    def _build_chain(self):
        """Build the RetrievalQA chain from the current vector store."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}      # Retrieve top 4 most relevant chunks
        )

        self.retrieval_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",         # "stuff" = put all chunks in one prompt
            retriever=retriever,
            return_source_documents=False
        )

    def query(self, question: str, history: list) -> str:
        """Answer a question using the stored document knowledge."""
        if self.vector_store is None:
            return ("❌ No document has been uploaded yet. "
                    "Please upload a PDF or TXT file first using the upload button.")

        # Run the retrieval + QA chain
        result = self.retrieval_chain.invoke({"query": question})
        return result["result"]
