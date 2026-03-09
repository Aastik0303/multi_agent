"""
tools/code_generator.py - Code Generation Tool
================================================
Handles:
  1. Generating code from natural language descriptions
  2. Explaining existing code
  3. Debugging assistance
  4. Supporting multiple programming languages
"""

from langchain.schema import SystemMessage, HumanMessage

# ── Use our central config — no .env, no os.getenv ───────────────────────────
from config import create_llm


class CodeGenerator:
    """
    Generates, explains, and debugs code using OpenRouter LLM.
    """

    def __init__(self):
        # Low temperature = consistent, deterministic code output
        self.llm = create_llm(temperature=0.2)

        # System prompt that makes the LLM a great coding assistant
        self.system_prompt = """You are an expert software engineer and coding assistant.
Your job is to:
1. Write clean, well-commented code when asked
2. Explain code clearly when asked to analyze it
3. Debug and fix code when asked
4. Follow best practices for the requested language
5. Always include:
   - Brief explanation of what the code does
   - The code block with proper syntax highlighting (```language ... ```)
   - Usage example if applicable
   - Any important notes or edge cases

Be concise but thorough. Format your response with clear sections."""

    def generate(self, message: str, history: list) -> str:
        """
        Generate or explain code based on user request.
        Includes recent history for multi-turn coding sessions.
        """
        # Build messages with conversation history
        messages = [SystemMessage(content=self.system_prompt)]

        # Add recent history (last 4 exchanges = 8 messages)
        for msg in history[-8:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(SystemMessage(content=f"Assistant: {msg['content']}"))

        # Add current request
        messages.append(HumanMessage(content=message))

        response = self.llm.invoke(messages)
        return response.content
