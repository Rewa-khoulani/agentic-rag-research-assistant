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
from sklearn.metrics.pairwise import cosine_similarity
tavily = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"))

# ================== دوال البحث (بدون/مع Rerank) ==================

def _search_paper_raw(query: str, section_filter: str = None, page_hint: int = None, top_k: int = 15) -> str:
    """استرجاع أولي من الورقة بدون Rerank."""
    results = retriever.retrieve(query, top_k=top_k, section_filter=section_filter, page_filter=page_hint)
    if not results["documents"] or not results["documents"][0]:
        print(f"⚠️ [_search_paper_raw] لا توجد نتائج لـ query='{query[:80]}...', section='{section_filter}', page='{page_hint}'")
        return ""
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    print(f"\n📋 [_search_paper_raw] استرجاع {len(docs)} قطعة:")
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        section = meta.get("section", "?")
        page = meta.get("page", "?")
        snippet = doc[:120].replace('\n', ' ')
        print(f"   {i+1}. page={page}, section='{section}' → {snippet}...")
    context = "\n\n".join([
        f"[Page {m.get('page', '?')} | {m.get('section', 'General')}]\n{t}"
        for t, m in zip(docs, metadatas)
    ])
    return context

# def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
#     """استرجاع متقدم مع إمكانية تعطيل Rerank."""
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
# def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
#     """استرجاع متقدم مع إمكانية تعطيل Rerank وتصفية تلقائية للقسم."""
    
#     # إذا لم يحدد المستخدم قسمًا يدويًا، نحاول تخمين أفضل قسم تلقائيًا
#     if not section_filter:
#         section_filter = _get_best_section_auto(query)
    
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
def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
    print(f"\n🔍 [_search_paper] query='{query[:100]}...', section_filter='{section_filter}', page_hint='{page_hint}', use_rerank={use_rerank}")
    if not section_filter:
        section_filter = _get_best_section_auto(query)
    if use_rerank:
        results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
        print(f"   [_search_paper] عدد النتائج الأولية: {len(results.get('documents', [[]])[0])}")
        reranked = retriever.rerank(query, results, top_k=top_k)
        if not reranked:
            print("   ❌ [_search_paper] لا توجد نتائج بعد إعادة الترتيب")
            return "No relevant information found in the paper."
        context = "\n\n".join([
            f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
            for r in reranked
        ])
        print(f"   ✅ [_search_paper] طول السياق النهائي: {len(context)} حرف")
        return context
    else:
        print("   ⚡ [_search_paper] استخدام الوضع الخام (بدون Rerank)")
        return _search_paper_raw(query, section_filter, page_hint, top_k=15)

def _web_search(query: str) -> str:
    return tavily.invoke({"query": query})

def _get_paper_sections() -> str:
    sections = retriever.get_available_sections()
    return "Available sections: " + ", ".join(sections)
# def _get_best_section_auto(query: str, threshold: float = 0.6) -> Optional[str]:
#     """
#     استخدام ChromaDB للعثور على أفضل اسم قسم مطابق للاستعلام.
#     تُستخدم فقط إذا لم يحدد المستخدم قسمًا يدويًا.
#     """
#     try:
#         query_emb = retriever.embedding_model.encode(query).tolist()
#         results = retriever.collection.query(
#             query_embeddings=[query_emb],
#             n_results=1,
#             where={"doc_type": "section_label"}
#         )
#         if results["documents"] and results["documents"][0]:
#             best_section = results["documents"][0][0]
#             # حساب تشابه cosine يدويًا لتطبيق العتبة
#             best_emb = retriever.embedding_model.encode(best_section)
#             similarity = cosine_similarity([query_emb], [best_emb.tolist()])[0][0]
#             if similarity >= threshold:
#                 print(f"🎯 [Auto-filter] تم اختيار القسم '{best_section}' تلقائيًا (تشابه: {similarity:.3f})")
#                 return best_section
#             else:
#                 print(f"🔸 [Auto-filter] أفضل قسم هو '{best_section}' لكن التشابه ({similarity:.3f}) أقل من العتبة ({threshold})")
#     except Exception as e:
#         print(f"⚠️ فشل البحث عن أفضل قسم: {e}")
#     return None
def _get_best_section_auto(query: str, threshold: float = 0.5) -> Optional[str]:
    """
    استخدام ChromaDB للعثور على أفضل اسم قسم مطابق للاستعلام.
    تُستخدم فقط إذا لم يحدد المستخدم قسمًا يدويًا.
    """
    try:
        query_emb = retriever.embedding_model.encode(query).tolist()
        # جلب جميع تسميات الأقسام من المجموعة
        all_section_results = retriever.collection.get(where={"doc_type": "section_label"})
        if not all_section_results["documents"]:
            print("⚠️ لا توجد تسميات أقسام مخزنة.")
            return None
        
        section_names = all_section_results["documents"]
        # حساب تضمينات الأقسام
        section_embs = retriever.embedding_model.encode(section_names)
        # حساب التشابه
        similarities = cosine_similarity([query_emb], section_embs)[0]
        
        # ترتيب الأقسام حسب التشابه
        sorted_idxs = similarities.argsort()[::-1]  # تنازليًا
        print(f"\n📊 [Auto-filter] تشابه الاستعلام مع الأقسام:")
        for i in sorted_idxs[:5]:  # عرض أفضل 5 أقسام
            print(f"   {section_names[i]}: {similarities[i]:.3f}")
        
        best_idx = sorted_idxs[0]
        best_section = section_names[best_idx]
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            print(f"🎯 [Auto-filter] تم اختيار القسم '{best_section}' تلقائيًا (تشابه: {best_score:.3f})")
            return best_section
        else:
            print(f"🔸 [Auto-filter] أفضل قسم هو '{best_section}' لكن التشابه ({best_score:.3f}) أقل من العتبة ({threshold})")
            return None
    except Exception as e:
        print(f"⚠️ فشل البحث عن أفضل قسم: {e}")
        return None
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