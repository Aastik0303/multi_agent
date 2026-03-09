"""
config.py - Centralized API Keys & Model Factory
==================================================
All credentials and model creation live here.
Every other file imports from this one — no .env needed.

OpenRouter acts as a unified gateway to 100s of models.
HuggingFace embeddings run locally — FREE, no API key needed.
"""

# ─── OpenRouter Credentials ───────────────────────────────────────────────────

OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model to use — this is a free 120B model via OpenRouter
OPENROUTER_MODEL = "'openai/gpt-oss-120b:free'"   # reliable free-tier model

# Max tokens for LLM responses
MAX_TOKENS = 2000

# ─── HuggingFace Embedding Model ─────────────────────────────────────────────
# This runs LOCALLY on your machine — completely free, no API key required.
# "all-MiniLM-L6-v2" is small (80MB), fast, and great for semantic search.
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ─── Factory Functions ────────────────────────────────────────────────────────
# Call these to get a ready-to-use LLM or embedding model.

def create_llm(temperature: float = 0.3, max_tokens: int = MAX_TOKENS):
    """
    Create and return a LangChain ChatOpenAI client pointed at OpenRouter.

    OpenRouter is OpenAI-API compatible, so we reuse ChatOpenAI
    but override the base_url and api_key.

    Usage:
        from config import create_llm
        llm = create_llm(temperature=0.7)
        response = llm.invoke([HumanMessage(content="Hello")])
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        default_headers={
            # OpenRouter recommends these headers for tracking / rate limits
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Multi-Agent RAG System",
        }
    )


def create_embeddings():
    """
    Create and return a HuggingFace embedding model.

    Runs 100% locally — no internet call, no API key.
    First run downloads the model (~80 MB) and caches it.

    Usage:
        from config import create_embeddings
        embedder = create_embeddings()
        vectors = embedder.embed_documents(["hello", "world"])
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},        # change to "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True}  # normalise for cosine similarity
    )
