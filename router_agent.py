"""
router_agent.py - The Brain of the System
==========================================
Detects user intent → routes to the correct agent.
Uses create_llm() from config.py (OpenRouter under the hood).
No .env file needed — credentials live in config.py.
"""

from langchain.schema import SystemMessage, HumanMessage

# ── Import from our central config (no .env needed) ──────────────────────────
from config import create_llm

# ── Import all specialized modules ───────────────────────────────────────────
from rag.document_rag     import DocumentRAG
from rag.youtube_rag      import YouTubeRAG
from agents.data_agent    import DataAgent
from tools.code_generator import CodeGenerator
from tools.research_tool  import ResearchTool


class RouterAgent:
    """
    Master router: classifies intent → delegates to the right tool.
    """

    def __init__(self):
        # ── Classifier LLM: low temp + tiny token budget = fast & cheap ──────
        self.classifier_llm = create_llm(temperature=0, max_tokens=20)

        # ── One instance of each specialized module ───────────────────────────
        self.document_rag   = DocumentRAG()
        self.youtube_rag    = YouTubeRAG()
        self.data_agent     = DataAgent()
        self.code_generator = CodeGenerator()
        self.research_tool  = ResearchTool()

        # ── Prompt that teaches the LLM to return exactly one label ──────────
        self.classifier_prompt = """You are an intent classifier.
Reply with EXACTLY ONE label — nothing else, no punctuation:

DOCUMENT_RAG   → user asks about an uploaded document / PDF / file
YOUTUBE_RAG    → user asks about a YouTube video or its transcript
DATA_ANALYSIS  → user wants CSV analysis, statistics, data insights
CODE_GENERATOR → user wants code written, explained, or debugged
DEEP_RESEARCH  → user wants a detailed, multi-step explanation or research
GENERAL_CHAT   → everything else

Reply with only the label."""

    # ─────────────────────────────────────────────────────────────────────────
    async def route(self, message: str, history: list) -> dict:
        """
        Public method called by main.py for every chat message.
        Returns {"answer": str, "agent_used": str}
        """
        intent = self._classify(message)
        print(f"[Router] Intent → {intent}")

        try:
            if intent == "DOCUMENT_RAG":
                return {"answer": self.document_rag.query(message, history),      "agent_used": "Document RAG"}

            elif intent == "YOUTUBE_RAG":
                return {"answer": self.youtube_rag.query(message, history),       "agent_used": "YouTube RAG"}

            elif intent == "DATA_ANALYSIS":
                return {"answer": self.data_agent.analyze(message),               "agent_used": "Data Analyst"}

            elif intent == "CODE_GENERATOR":
                return {"answer": self.code_generator.generate(message, history), "agent_used": "Code Generator"}

            elif intent == "DEEP_RESEARCH":
                return {"answer": self.research_tool.research(message, history),  "agent_used": "Deep Research"}

            else:
                return {"answer": self._general_chat(message, history),           "agent_used": "General Chat"}

        except Exception as e:
            print(f"[Router] Agent failed ({intent}): {e} — falling back to general chat")
            return {"answer": self._general_chat(message, history), "agent_used": "General Chat (fallback)"}

    # ─────────────────────────────────────────────────────────────────────────
    def _classify(self, message: str) -> str:
        """Send the message to the classifier LLM and get a label back."""
        try:
            resp = self.classifier_llm.invoke([
                SystemMessage(content=self.classifier_prompt),
                HumanMessage(content=f"User message: {message}")
            ])
            label = resp.content.strip().upper()
            valid = {"DOCUMENT_RAG", "YOUTUBE_RAG", "DATA_ANALYSIS",
                     "CODE_GENERATOR", "DEEP_RESEARCH", "GENERAL_CHAT"}
            return label if label in valid else "GENERAL_CHAT"
        except Exception as e:
            print(f"[Router] Classification error: {e}")
            return "GENERAL_CHAT"

    # ─────────────────────────────────────────────────────────────────────────
    def _general_chat(self, message: str, history: list) -> str:
        """Friendly general-purpose chat with short-term memory."""
        chat_llm = create_llm(temperature=0.7)

        messages = [SystemMessage(content=(
            "You are a helpful, friendly AI assistant. "
            "Be concise, accurate, and clear."
        ))]

        # Inject last 3 exchanges (6 messages) as context
        for msg in history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(SystemMessage(content=f"Assistant: {msg['content']}"))

        messages.append(HumanMessage(content=message))
        return chat_llm.invoke(messages).content
