
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from backend.core.retriever import retriever
from config import TAVILY_API_KEY
import os
from sklearn.metrics.pairwise import cosine_similarity
tavily = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY or os.getenv("TAVILY_API_KEY"))
from typing import List, Optional
# ================== دوال البحث (بدون/مع Rerank) ==================

def _search_paper_raw(query: str, section_filter: str = None, page_hint: int = None, top_k: int = 15) -> str:
    """استرجاع أولي من الورقة بدون Rerank."""
    results = retriever.retrieve(query, top_k=top_k, section_filter=section_filter, page_filter=page_hint)
    if not results["documents"] or not results["documents"][0]:
        print(f"⚠️ [_search_paper_raw]    no result query='{query[:80]}...', section='{section_filter}', page='{page_hint}'")
        return ""
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    print(f"\n📋 [_search_paper_raw] retreve {len(docs)} chunk:")
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
# def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
#     print(f"\n🔍 [_search_paper] query='{query[:100]}...', section_filter='{section_filter}', page_hint='{page_hint}', use_rerank={use_rerank}")
#     if not section_filter:
#         section_filter = _get_best_section_auto(query)
#     if use_rerank:
#         results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
#         print(f"   [_search_paper] عدد النتائج الأولية: {len(results.get('documents', [[]])[0])}")
#         reranked = retriever.rerank(query, results, top_k=top_k)
#         if not reranked:
#             print("   ❌ [_search_paper] لا توجد نتائج بعد إعادة الترتيب")
#             return "No relevant information found in the paper."
#         context = "\n\n".join([
#             f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
#             for r in reranked
#         ])
#         print(f"   ✅ [_search_paper] طول السياق النهائي: {len(context)} حرف")
#         return context
#     else:
#         print("   ⚡ [_search_paper] استخدام الوضع الخام (بدون Rerank)")
#         return _search_paper_raw(query, section_filter, page_hint, top_k=15)
def _search_paper(query: str, section_filter: str = None, page_hint: int = None, use_rerank: bool = True, top_k: int = 5) -> str:
    print(f"\n🔍 [_search_paper] query='{query[:100]}...', section_filter='{section_filter}', page_hint='{page_hint}', use_rerank={use_rerank}")
    
    sections_to_search = []
    if not section_filter:
        sections_to_search = _get_best_sections_auto(query)
    
    if use_rerank:
        all_docs = []
        all_metas = []
        
        if sections_to_search:
            for sec in sections_to_search:
                results = retriever.retrieve(query, top_k=10, section_filter=sec, page_filter=page_hint)
                if results["documents"] and results["documents"][0]:
                    all_docs.extend(results["documents"][0])
                    all_metas.extend(results["metadatas"][0])
        else:
            results = retriever.retrieve(query, top_k=15, section_filter=section_filter, page_filter=page_hint)
            if results["documents"] and results["documents"][0]:
                all_docs = results["documents"][0]
                all_metas = results["metadatas"][0]
        
        if not all_docs:
            print("   ❌ [_search_paper] no  result   ")
            return "No relevant information found in the paper."
        
        print(f"   [_search_paper]   count of results: {len(all_docs)}")
        
        reranked = retriever.rerank(query, {"documents": [all_docs], "metadatas": [all_metas]}, top_k=top_k)
        if not reranked:
            return "No relevant information found in the paper."
        
        context = "\n\n".join([
            f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
            for r in reranked
        ])
        print(f"   ✅ [_search_paper]   context length: {len(context)} caracter")
        return context
    else:
        return _search_paper_raw(query, section_filter, page_hint, top_k=15)

def _web_search(query: str) -> str:
    return tavily.invoke({"query": query})

def _get_paper_sections() -> str:
    sections = retriever.get_available_sections()
    return "Available sections: " + ", ".join(sections)
def search_paper_hybrid(query: str, page_hint: int = None, top_k: int = 5) -> str:
    """بحث هجين (Vector + BM25) مع Rerank."""
    print(f"\n🔍 [_search_paper_hybrid] query='{query[:100]}...'")
    
    # 1. استرجاع متجهي (بدون تسميات الأقسام)
    
    vector_results = retriever.retrieve(
    query, top_k=15,
    section_filter=None, page_filter=page_hint,
    where_filter1={"doc_type": {"$ne": "section_label"}}
)
    # 2. استرجاع BM25
    bm25_results = retriever.bm25_search(query, top_k=15)
    
    # دمج النتائج وإزالة التكرار
    all_docs = []
    all_metas = []
    seen_texts = set()
    
    # إضافة نتائج BM25 أولاً (لنحتفظ بترتيبها إن أمكن)
    for text, _ in bm25_results:
        if text not in seen_texts:
            seen_texts.add(text)
            all_docs.append(text)
            # بيانات وصفية افتراضية (يمكن تحسينها بحفظها مع BM25)
            all_metas.append({"page": "?", "section": "General"})
    
    # إضافة نتائج المتجهات (من ChromaDB)
    if vector_results["documents"] and vector_results["documents"][0]:
        for doc, meta in zip(vector_results["documents"][0], vector_results["metadatas"][0]):
            if doc not in seen_texts:
                seen_texts.add(doc)
                all_docs.append(doc)
                all_metas.append(meta)
    
    if not all_docs:
        return "No relevant information found in the paper."
    
    print(f"   [_search_paper_hybrid]   total results after merg : {len(all_docs)}")
    
    # Rerank على النتائج المجمعة
    reranked = retriever.rerank(query, {"documents": [all_docs], "metadatas": [all_metas]}, top_k=top_k)
    if not reranked:
        return "No relevant information found in the paper."
    
    context = "\n\n".join([
        f"[Page {r['metadata'].get('page', '?')} | {r['metadata'].get('section', 'General')}]\n{r['text']}"
        for r in reranked
    ])
    print(f"   ✅ [_search_paper_hybrid]  context final length : {len(context)} character")
    return context
def _get_best_sections_auto(query: str, threshold: float = 0.6) -> List[str]:
    try:
        all_section_results = retriever.collection.get(where={"doc_type": "section_label"})
        if not all_section_results["documents"]:
            print("⚠️ no stored section")
            return []
        
        section_names = all_section_results["documents"]
        response = retriever.co_client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=section_names,
            top_n=len(section_names)
        )
        
        scored = [(res.relevance_score, section_names[res.index]) for res in response.results]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\n📊 [Auto-filter]    Reranker (Cohere):")
        for score, sec in scored[:5]:
            print(f"   {sec}: {score:.4f}")
        
        best_sections = [sec for score, sec in scored if score >= threshold]
        if best_sections:
            print(f"🎯 [Auto-filter] selected {len(best_sections)} sections: {best_sections}")
            return best_sections
        else:
            print(f"🔸 [Auto-filter] no sections that exceed threshold({threshold})")
            return []
    except Exception as e:
        print(f"⚠️ فشل البحث عن أفضل قسم: {e}")
        return []
# def _get_best_section_auto(query: str, threshold: float = 0.5) -> Optional[str]:
#     """
#     استخدام ChromaDB للعثور على أفضل اسم قسم مطابق للاستعلام.
#     تُستخدم فقط إذا لم يحدد المستخدم قسمًا يدويًا.
#     """
#     try:
#         query_emb = retriever.embedding_model.encode(query).tolist()
#         # جلب جميع تسميات الأقسام من المجموعة
#         all_section_results = retriever.collection.get(where={"doc_type": "section_label"})
#         if not all_section_results["documents"]:
#             print("⚠️ لا توجد تسميات أقسام مخزنة.")
#             return None
        
#         section_names = all_section_results["documents"]
#         # حساب تضمينات الأقسام
#         section_embs = retriever.embedding_model.encode(section_names)
#         # حساب التشابه
#         similarities = cosine_similarity([query_emb], section_embs)[0]
        
#         # ترتيب الأقسام حسب التشابه
#         sorted_idxs = similarities.argsort()[::-1]  # تنازليًا
#         print(f"\n📊 [Auto-filter] تشابه الاستعلام مع الأقسام:")
#         for i in sorted_idxs[:5]:  # عرض أفضل 5 أقسام
#             print(f"   {section_names[i]}: {similarities[i]:.3f}")
        
#         best_idx = sorted_idxs[0]
#         best_section = section_names[best_idx]
#         best_score = similarities[best_idx]
        
#         if best_score >= threshold:
#             print(f"🎯 [Auto-filter] تم اختيار القسم '{best_section}' تلقائيًا (تشابه: {best_score:.3f})")
#             return best_section
#         else:
#             print(f"🔸 [Auto-filter] أفضل قسم هو '{best_section}' لكن التشابه ({best_score:.3f}) أقل من العتبة ({threshold})")
#             return None
#     except Exception as e:
#         print(f"⚠️ فشل البحث عن أفضل قسم: {e}")
#         return None
    
def sort_chunks_by_chunk_id(initial_results):
    """تأخذ نتائج الاسترجاع الأولية وتعيد النصوص مرتبة حسب chunk_id."""
    if not initial_results.get("documents") or not initial_results["documents"][0]:
        return []
    
    docs = initial_results["documents"][0]
    metas = initial_results["metadatas"][0]
    combined = list(zip(docs, metas))
    
    # فرز حسب chunk_id (الترتيب الأصلي للقطعة)
    combined.sort(key=lambda x: int(x[1].get("chunk_id", 0)))
    
    return [item[0] for item in combined], [item[1] for item in combined]
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