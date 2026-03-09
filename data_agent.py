"""
agents/data_agent.py - Data Analyst Agent
==========================================
Handles:
  1. Loading CSV files into pandas DataFrames
  2. Generating automatic summary statistics
  3. Answering questions about the data using LLM
  4. Providing insights and analysis
"""

import io
import pandas as pd
from langchain.schema import SystemMessage, HumanMessage

# ── Use our central config — no .env, no os.getenv ───────────────────────────
from config import create_llm


class DataAgent:
    """
    Analyzes CSV data using pandas and answers questions with LLM assistance.
    Uses OpenRouter LLM via config.py.
    """

    def __init__(self):
        self.llm      = create_llm(temperature=0.3)
        self.df = None              # Current loaded DataFrame
        self.filename = None        # Name of the loaded file

    def load_csv(self, file_bytes: bytes, filename: str) -> str:
        """
        Load a CSV file into a pandas DataFrame.
        Returns a summary of what was loaded.
        """
        try:
            # Read CSV from bytes
            self.df = pd.read_csv(io.BytesIO(file_bytes))
            self.filename = filename

            rows, cols = self.df.shape
            print(f"[DataAgent] Loaded {rows} rows × {cols} columns from '{filename}'")

            return (f"✅ CSV loaded successfully!\n"
                    f"📊 **{rows} rows × {cols} columns**\n"
                    f"📋 Columns: {', '.join(self.df.columns.tolist())}\n\n"
                    f"You can now ask questions like:\n"
                    f"- 'Show me summary statistics'\n"
                    f"- 'What are the top 5 rows?'\n"
                    f"- 'What is the average of [column]?'\n"
                    f"- 'Find missing values'\n"
                    f"- 'What insights can you find?'")

        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")

    def _get_dataframe_context(self) -> str:
        """
        Build a text description of the DataFrame for the LLM.
        We can't send the whole DataFrame, so we send a summary.
        """
        if self.df is None:
            return "No data loaded."

        lines = []
        lines.append(f"Dataset: {self.filename}")
        lines.append(f"Shape: {self.df.shape[0]} rows × {self.df.shape[1]} columns")
        lines.append(f"Columns: {list(self.df.columns)}")
        lines.append(f"Data types:\n{self.df.dtypes.to_string()}")

        # Numeric summary
        numeric_cols = self.df.select_dtypes(include="number")
        if not numeric_cols.empty:
            lines.append(f"\nNumeric Summary:\n{numeric_cols.describe().round(2).to_string()}")

        # Missing values
        missing = self.df.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            lines.append(f"\nMissing Values:\n{missing.to_string()}")
        else:
            lines.append("\nMissing Values: None")

        # Sample rows (first 5)
        lines.append(f"\nFirst 5 rows:\n{self.df.head().to_string()}")

        return "\n".join(lines)

    def analyze(self, question: str) -> str:
        """
        Answer a question about the loaded CSV data.
        """
        if self.df is None:
            return ("❌ No CSV file has been uploaded yet. "
                    "Please upload a CSV file first using the upload button.")

        # Build context from the DataFrame
        data_context = self._get_dataframe_context()

        # Ask the LLM to analyze with the data context
        messages = [
            SystemMessage(content=f"""You are an expert data analyst. 
You have access to the following dataset information:

{data_context}

Answer the user's question about this data. Be specific, use numbers from the data,
and provide actionable insights. Format your answer clearly with markdown."""),
            HumanMessage(content=question)
        ]

        response = self.llm.invoke(messages)
        return response.content
