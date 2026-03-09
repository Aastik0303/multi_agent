"""
tools/code_generator.py  —  Agentic Code Writer & Debugger
============================================================
Built with LangChain's initialize_agent + AgentExecutor.

The agent has 4 Tools it picks from automatically:
  1. WriteCode    — generate new code from a description
  2. ExplainCode  — explain what a piece of code does
  3. DebugCode    — find bugs and return fixed code
  4. RunPython    — safely execute Python via PythonREPLTool and return output

Thought → Action → Observation loop (ReAct pattern) means the agent
can write code, run it, see the output, then fix errors automatically.
"""

from langchain.agents  import initialize_agent, AgentType, Tool
from langchain.memory  import ConversationBufferWindowMemory
from langchain.schema  import SystemMessage, HumanMessage
from langchain_experimental.tools import PythonREPLTool

from config import create_llm


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_write_code(description: str) -> str:
    """
    Call the LLM to write clean, commented code from a plain-English description.
    Returns the code + a brief explanation.
    """
    llm = create_llm(temperature=0.15, max_tokens=1200)
    prompt = f"""Write clean, well-commented code for the following task.

Task: {description}

Rules:
- Add inline comments explaining key lines
- Include a usage/example at the bottom in a comment block
- Use best practices for the language (default Python unless specified)
- Format the code block with triple backticks and language name
"""
    return llm.invoke([SystemMessage(content=prompt)]).content


def tool_explain_code(code: str) -> str:
    """
    Call the LLM to explain what a piece of code does in plain English.
    """
    llm = create_llm(temperature=0.3, max_tokens=800)
    prompt = f"""Explain the following code clearly.

Cover:
1. What it does overall (1-2 sentences)
2. How it works step-by-step
3. Any important patterns or tricks used
4. Potential issues or edge cases

Code:
{code}
"""
    return llm.invoke([SystemMessage(content=prompt)]).content


def tool_debug_code(code_and_error: str) -> str:
    """
    Receive code (and optionally an error message) and return fixed code.
    Input format: 'CODE\n---\nERROR' or just 'CODE' if no error message.
    """
    llm = create_llm(temperature=0.1, max_tokens=1200)
    prompt = f"""You are an expert debugger. Find and fix all bugs in the code below.

Input (code, optionally followed by --- and the error message):
{code_and_error}

Return:
1. What was wrong (bullet points)
2. The fixed code in a properly formatted code block
3. What changed and why
"""
    return llm.invoke([SystemMessage(content=prompt)]).content


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class CodeGenerator:
    """
    Agentic Code Writer & Debugger.
    Uses initialize_agent with CONVERSATIONAL_REACT_DESCRIPTION so it can
    chain tools across turns (e.g. write → run → debug automatically).
    """

    def __init__(self):
        self.llm = create_llm(temperature=0.1, max_tokens=1500)

        # PythonREPLTool runs Python snippets in a subprocess and returns stdout
        python_repl = PythonREPLTool()

        self.tools = [
            Tool(
                name="WriteCode",
                func=tool_write_code,
                description=(
                    "Use this to write new code from a description. "
                    "Input: a plain-English description of what the code should do."
                )
            ),
            Tool(
                name="ExplainCode",
                func=tool_explain_code,
                description=(
                    "Use this to explain what a piece of code does. "
                    "Input: the code as a string."
                )
            ),
            Tool(
                name="DebugCode",
                func=tool_debug_code,
                description=(
                    "Use this to find and fix bugs in code. "
                    "Input: the buggy code, optionally followed by '---' and the error message."
                )
            ),
            Tool(
                name="RunPython",
                func=python_repl.run,
                description=(
                    "Use this to actually EXECUTE a Python code snippet and see its output. "
                    "Useful for verifying that generated code works. "
                    "Input: valid Python code as a string."
                )
            ),
        ]

        # Memory: keep last 6 exchanges so the agent remembers previous code
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=6,
            return_messages=True
        )

        # Build the ReAct agent
        self.agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=8,
        )

    def generate(self, message: str, history: list) -> str:
        """Run the coding agent on the user's request."""
        try:
            return self.agent_executor.run(message)
        except Exception as e:
            return f"❌ Code agent error: {e}"