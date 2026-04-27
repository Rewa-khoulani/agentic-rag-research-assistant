# from langchain_openai import ChatOpenAI
# from config import OPENAI_API_KEY

# llm = ChatOpenAI(
#     model="gpt-4o",
#     temperature=0,
#     api_key=OPENAI_API_KEY
# )
# from langchain_groq import ChatGroq
# from config import GROQ_API_KEY
# import os

# llm = ChatGroq(
#     model="llama3-8b-8192",      # أو llama3-70b-8192 للأداء الأقوى
#     temperature=0,
#     api_key=GROQ_API_KEY or os.getenv("GROQ_API_KEY")
# )


# from langchain_huggingface import HuggingFaceEndpoint
# from config import HF_API_KEY
# import os

# llm = HuggingFaceEndpoint(
#     repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
#     max_new_tokens=512,
#     temperature=0.01,
#     huggingfacehub_api_token=HF_API_KEY or os.getenv("HF_TOKEN")
# )
# from langchain_google_genai import ChatGoogleGenerativeAI
# from config import GOOGLE_API_KEY

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-lite",
#     temperature=0,
#     google_api_key=GOOGLE_API_KEY
# )

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma2:2b ",
    temperature=0,
    format="json",           # مهم جداً لدعم with_structured_output
    num_predict=2048,
)