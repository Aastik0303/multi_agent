"""
tools/research_tool.py - Deep Research Tool
=============================================
Handles:
  1. Multi-step reasoning on complex topics
  2. Structured, detailed explanations
  3. Comparison and analysis
  4. Comprehensive answers with sources of thought

The "deep research" approach breaks the question into sub-questions,
answers each one, then synthesizes a comprehensive response.
"""

from langchain.schema import SystemMessage, HumanMessage

# ── Use our central config — no .env, no os.getenv ───────────────────────────
from config import create_llm


class ResearchTool:
    """
    Multi-step reasoning tool for deep research questions.
    Uses OpenRouter LLM via config.py.
    """

    def __init__(self):
        self.llm = create_llm(temperature=0.5)

    def research(self, question: str, history: list) -> str:
        """
        Perform deep research using a two-step approach:
          Step 1: Break the question into sub-questions
          Step 2: Answer each sub-question
          Step 3: Synthesize into a comprehensive answer
        """
        # Step 1: Generate a research plan (sub-questions)
        plan = self._generate_research_plan(question)

        # Step 2: Execute the research plan and synthesize
        answer = self._synthesize_answer(question, plan, history)

        return answer

    def _generate_research_plan(self, question: str) -> str:
        """Break the main question into 3-5 focused sub-questions."""
        messages = [
            SystemMessage(content="""You are a research planner. 
Given a question, break it down into 3-5 specific sub-questions that together 
will fully answer the main question. Be concise. Format as a numbered list."""),
            HumanMessage(content=f"Question: {question}")
        ]
        response = self.llm.invoke(messages)
        return response.content

    def _synthesize_answer(self, question: str, plan: str, history: list) -> str:
        """Use the research plan to write a comprehensive, structured answer."""

        # Build history context
        history_context = ""
        for msg in history[-4:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_context += f"{role}: {msg['content']}\n"

        messages = [
            SystemMessage(content=f"""You are an expert researcher and writer.
You have broken down the question into sub-questions:

{plan}

Now write a comprehensive, well-structured answer that:
1. Addresses all sub-questions
2. Uses clear headings (##) for each major section
3. Provides concrete examples where helpful
4. Concludes with a summary
5. Is accurate and balanced

Previous conversation context:
{history_context if history_context else "None"}"""),
            HumanMessage(content=f"Please research and answer: {question}")
        ]

        response = self.llm.invoke(messages)
        return response.content
