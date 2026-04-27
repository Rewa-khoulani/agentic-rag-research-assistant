from fastapi import FastAPI
from langserve import add_routes
import uvicorn
from dotenv import load_dotenv
from pathlib import Path
import sys

parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from backend.ai.graphs import master_graph

load_dotenv()

app = FastAPI(
    title="Research Paper Assistant",
    version="1.0",
    description="Agentic RAG for research papers."
)

add_routes(
    app,
    master_graph,
    path="/paper-assistant",
)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)