import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ChromaDB
CHROMA_PERSIST_DIR = Path("./chroma_db")
COLLECTION_NAME = "papers"

# API Keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_API_KEY = os.getenv("HF_TOKEN", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

# Models
EMBEDDING_MODEL_NAME = "allenai-specter"
LLM_MODEL_NAME = "gpt-4o"  # أو أي نموذج OpenAI متوافق

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50