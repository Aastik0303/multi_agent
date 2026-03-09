"""
rag/youtube_rag.py - YouTube Transcript RAG Pipeline
======================================================
Handles:
  1. Accepting a YouTube URL
  2. Extracting the video transcript
  3. Chunking and embedding the transcript
  4. Answering questions about the video
"""

import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# ── Use our central config — no .env, no os.getenv ───────────────────────────
from config import create_llm, create_embeddings


class YouTubeRAG:
    """
    RAG pipeline for YouTube videos.
    Uses HuggingFace embeddings (local, free) + OpenRouter LLM.
    """

    def __init__(self):
        self.embeddings = create_embeddings()
        self.llm        = create_llm(temperature=0.3)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80
        )
        self.vector_store = None
        self.retrieval_chain = None
        self.current_video_title = None

    def _extract_video_id(self, url: str) -> str:
        """
        Extract YouTube video ID from various URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/shorts/VIDEO_ID
        """
        patterns = [
            r"(?:v=)([a-zA-Z0-9_-]{11})",         # Standard URL
            r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",  # Short URL
            r"(?:shorts/)([a-zA-Z0-9_-]{11})",      # Shorts URL
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from URL: {url}")

    def ingest(self, url: str) -> str:
        """
        Process a YouTube video:
          1. Extract video ID
          2. Download transcript
          3. Chunk and embed
          4. Store in FAISS
        """
        # Step 1: Get video ID
        video_id = self._extract_video_id(url)
        print(f"[YouTubeRAG] Processing video ID: {video_id}")

        # Step 2: Fetch transcript
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except TranscriptsDisabled:
            raise ValueError("This video has transcripts disabled. Try another video.")
        except NoTranscriptFound:
            raise ValueError("No transcript found for this video (it may not have captions).")

        # Step 3: Combine transcript segments into full text
        # Each segment is: {"text": "...", "start": 12.5, "duration": 2.0}
        full_text = " ".join([seg["text"] for seg in transcript_list])
        print(f"[YouTubeRAG] Transcript length: {len(full_text)} characters")

        # Step 4: Wrap in a LangChain Document object with metadata
        doc = Document(
            page_content=full_text,
            metadata={"source": url, "video_id": video_id}
        )

        # Step 5: Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        print(f"[YouTubeRAG] Split into {len(chunks)} chunks")

        # Step 6: Create vector store
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)

        # Step 7: Build chain
        self._build_chain()

        return f"✅ YouTube video processed successfully! ({len(chunks)} chunks indexed). You can now ask questions about the video."

    def _build_chain(self):
        """Build the QA chain."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        self.retrieval_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False
        )

    def query(self, question: str, history: list) -> str:
        """Answer a question about the YouTube video."""
        if self.vector_store is None:
            return ("❌ No YouTube video has been processed yet. "
                    "Please enter a YouTube URL first.")

        result = self.retrieval_chain.invoke({"query": question})
        return result["result"]
