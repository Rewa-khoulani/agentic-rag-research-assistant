# # from langchain_core.tools import tool
# # from langchain_tavily import TavilySearch
# # from backend.core.retriever import retriever
# # from config import TAVILY_API_KEY
# # import os

# # tavily = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"))

# # @tool
# # def search_paper(query: str, section_filter: str = None, page_hint: int = None) -> str:
# #     """
# #     Search the loaded research paper for relevant information.
# #     Use section_filter to limit search to a specific section.
# #     Use page_hint to limit to a specific page number.
# #     """
# #     results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
# #     reranked = retriever.rerank(query, results, top_k=5)
# #     if not reranked:
# #         return "No relevant information found in the paper."
# #     context = "\n\n".join([
# #         f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
# #         for r in reranked
# #     ])
# #     return context

# # @tool
# # def web_search(query: str) -> str:
# #     """
# #     Search the web for external information not found in the paper.
# #     """
# #     return tavily.invoke({"query": query})

# # @tool
# # def get_paper_sections() -> str:
# #     """Return a list of available sections in the loaded paper."""
# #     sections = retriever.get_available_sections()
# #     return "Available sections: " + ", ".join(sections)

# from langchain_core.tools import tool
# from langchain_tavily import TavilySearch
# from backend.core.retriever import retriever
# from config import TAVILY_API_KEY
# import os

# tavily = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"))

# # تعريف الدوال الأساسية التي ستستخدم داخلياً ومن قبل الأدوات
# # def _search_paper(query: str, section_filter: str = None, page_hint: int = None) -> str:
# #     results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
# #     reranked = retriever.rerank(query, results, top_k=5)
# #     if not reranked:
# #         return "No relevant information found in the paper."
# #     context = "\n\n".join([
# #         f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
# #         for r in reranked
# #     ])
# #     print(f"\n🔎 [Tool: search_paper] query='{query}', section='{section_filter}', page={page_hint}")
# #     return context
# # ... (بقية الملف كما هو)

# def _search_paper_raw(query: str, section_filter: str = None, page_hint: int = None, top_k: int = 15) -> str:
#     results = retriever.retrieve(query, top_k=top_k, section_filter=section_filter, page_filter=page_hint)
#     if not results["documents"] or not results["documents"][0]:
#         return ""
#     docs = results["documents"][0]
#     metadatas = results["metadatas"][0]
#     context = "\n\n".join([
#         f"[Page {m.get('page', '?')} | {m.get('section', 'General')}]\n{t}"
#         for t, m in zip(docs, metadatas)
#     ])
#     return context

# def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
#     if use_rerank:
#         results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
#         reranked = retriever.rerank(query, results, top_k=top_k)
#         if not reranked:
#             return "No relevant information found in the paper."
#         context = "\n\n".join([
#             f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
#             for r in reranked
#         ])
#         return context
#     else:
#         return _search_paper_raw(query, section_filter, page_hint, top_k=15)

# # تحديث الأدوات لتمرير بارامترات إضافية (اختياري)
# @tool
# def search_paper(query: str, section_filter: str = None, page_hint: int = None) -> str:
#     return _search_paper(query, section_filter, page_hint, use_rerank=True)

# @tool
# def search_paper_no_rerank(query: str, section_filter: str = None, page_hint: int = None) -> str:
#     return _search_paper(query, section_filter, page_hint, use_rerank=False)
# def _web_search(query: str) -> str:
#     print(f"\n🌐 [Tool: web_search] query='{query}'")
#     return tavily.invoke({"query": query})

# def _get_paper_sections() -> str:
#     sections = retriever.get_available_sections()
    
#     return "Available sections: " + ", ".join(sections)

# # تحويلها إلى أدوات LangChain
# # @tool
# # def search_paper(query: str, section_filter: str = None, page_hint: int = None) -> str:
# #     """
# #     Search the loaded research paper for relevant information.
# #     Use section_filter to limit search to a specific section.
# #     Use page_hint to limit to a specific page number.
# #     """
# #     return _search_paper(query, section_filter, page_hint)

# @tool
# def web_search(query: str) -> str:
#     """
#     Search the web for external information not found in the paper.
#     """
#     return _web_search(query)

# @tool
# def get_paper_sections() -> str:
#     """Return a list of available sections in the loaded paper."""
#     return _get_paper_sections()
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from backend.core.retriever import retriever
from config import TAVILY_API_KEY
import os

tavily = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"))

# ================== دوال البحث (بدون/مع Rerank) ==================

def _search_paper_raw(query: str, section_filter: str = None, page_hint: int = None, top_k: int = 15) -> str:
    """استرجاع أولي من الورقة بدون Rerank."""
    results = retriever.retrieve(query, top_k=top_k, section_filter=section_filter, page_filter=page_hint)
    if not results["documents"] or not results["documents"][0]:
        return ""
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    context = "\n\n".join([
        f"[Page {m.get('page', '?')} | {m.get('section', 'General')}]\n{t}"
        for t, m in zip(docs, metadatas)
    ])
    return context

def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
    """استرجاع متقدم مع إمكانية تعطيل Rerank."""
    if use_rerank:
        results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
        reranked = retriever.rerank(query, results, top_k=top_k)
        if not reranked:
            return "No relevant information found in the paper."
        context = "\n\n".join([
            f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
            for r in reranked
        ])
        return context
    else:
        return _search_paper_raw(query, section_filter, page_hint, top_k=15)

def _web_search(query: str) -> str:
    return tavily.invoke({"query": query})

def _get_paper_sections() -> str:
    sections = retriever.get_available_sections()
    return "Available sections: " + ", ".join(sections)

# ================== أدوات LangChain ==================

@tool
def search_paper(query: str, section_filter: str = None, page_hint: int = None) -> str:
    """Search the loaded research paper for relevant information (with Rerank)."""
    return _search_paper(query, section_filter, page_hint, use_rerank=True)

@tool
def search_paper_no_rerank(query: str, section_filter: str = None, page_hint: int = None) -> str:
    """Search the loaded research paper WITHOUT Rerank (faster, for bulk retrieval)."""
    return _search_paper(query, section_filter, page_hint, use_rerank=False)

@tool
def web_search(query: str) -> str:
    """Search the web for external information not found in the paper."""
    return _web_search(query)

@tool
def get_paper_sections() -> str:
    """Return a list of available sections in the loaded paper."""
    return _get_paper_sections()