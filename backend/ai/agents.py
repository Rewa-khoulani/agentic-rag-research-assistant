# import logging
# from pydantic import BaseModel, Field
# from typing import Literal, Optional
# from langchain_core.messages import HumanMessage

# from backend.core import llm
# from backend.ai.state import PaperState, TeamState
# from backend.ai.tools import search_paper, web_search, get_paper_sections
# from backend.ai.prompts import (
#     classifier_prompt, paper_qa_prompt, locate_paragraph_prompt,
#     full_summary_prompt, web_merge_prompt, critic_prompt
# )

# from backend.ai.tools import _search_paper as search_paper, _web_search as web_search, _get_paper_sections as get_paper_sections
# logger = logging.getLogger(__name__)

# # ------------------- Classifier Node -------------------
# class IntentClassification(BaseModel):
#     intent: Literal["locate_paragraph", "full_summary", "paper_qa", "external_concept", "chat"]
#     section: Optional[str] = Field(None, description="The section mentioned in the query, if any")
#     page_hint: Optional[int] = Field(None, description="The page number mentioned, if any")

# def classifier_node(state: TeamState):
#     messages = state.get("messages", [])
#     if not messages:
#         return {"next_step": "chat"}

#     last_msg = messages[-1]
#     content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

#     structured_llm = llm.with_structured_output(IntentClassification)
#     formatted = classifier_prompt.format_messages(input=content)
#     result = structured_llm.invoke(formatted)

#     logger.info(f"Classifier from query: intent={result.intent}, section={result.section}, page={result.page_hint}")

#     # **الأولوية للاختيار اليدوي إن وجد في الحالة**
#     manual_section = state.get("section_filter")
#     manual_page = state.get("page_hint")

#     final_section = manual_section if manual_section is not None else result.section
#     final_page = manual_page if manual_page is not None else result.page_hint

#     logger.info(f"Final filter: section={final_section}, page={final_page}")

#     if not state.get("paper_loaded") and result.intent != "chat":
#         return {
#             "next_step": "chat",
#             "messages": [HumanMessage(content="Please upload a paper first.")]
#         }

#     return {
#         "next_step": result.intent,
#         "section_filter": final_section,
#         "page_hint": final_page
#     }

# # ------------------- Chatbot Node -------------------
# def chatbot_node(state: TeamState):
#     messages = state["messages"]
#     response = llm.invoke(messages)
#     return {"messages": [response]}

# # ------------------- Paper QA Agent (RAG) -------------------
# def paper_qa_node(state: PaperState):
#     logger.info(f"--- Paper QA: answering question ---")
#     query = state["query"]
#     section = state.get("section_filter")
#     page = state.get("page_hint")

#     context = search_paper.invoke({
#         "query": query,
#         "section_filter": section,
#         "page_hint": page
#     })

#     formatted = paper_qa_prompt.format_messages(context=context, query=query)
#     response = llm.invoke(formatted)
#     return {"draft_answer": response.content, "retrieved_context": context}

# # ------------------- Locate Paragraph Node -------------------
# def locate_paragraph_node(state: PaperState):
#     logger.info(f"--- Locate Paragraph: finding specific paragraph ---")
#     query = state["query"]
#     page = state.get("page_hint")
#     context = search_paper.invoke({
#         "query": query,
#         "page_hint": page
#     })
#     formatted = locate_paragraph_prompt.format_messages(context=context, query=query)
#     response = llm.invoke(formatted)
#     return {"draft_answer": response.content, "retrieved_context": context}

# # ------------------- Full Summary Node -------------------
# def full_summary_node(state: PaperState):
#     logger.info(f"--- Full Summary: summarizing entire paper ---")
#     sections_str = get_paper_sections.invoke({})
#     try:
#         sections = sections_str.replace("Available sections: ", "").split(", ")
#     except:
#         sections = []
#     context_parts = []
#     for sec in sections:
#         sec_context = search_paper.invoke({
#             "query": f"summary of {sec}",
#             "section_filter": sec
#         })
#         context_parts.append(f"=== {sec} ===\n{sec_context}")
#     context = "\n\n".join(context_parts)
#     formatted = full_summary_prompt.format_messages(context=context)
#     response = llm.invoke(formatted)
#     return {"draft_answer": response.content, "retrieved_context": context}

# # ------------------- External Concept Node (Web) -------------------
# def external_concept_node(state: PaperState):
#     logger.info(f"--- External Concept: searching web ---")
#     query = state["query"]
#     web_data = web_search.invoke({"query": query})
#     paper_context = search_paper.invoke({"query": query})
#     formatted = web_merge_prompt.format_messages(
#         paper_context=paper_context,
#         web_data=web_data,
#         query=query
#     )
#     response = llm.invoke(formatted)
#     return {"draft_answer": response.content, "raw_data": web_data}

# # ------------------- Critic Node -------------------
# class CriticOutput(BaseModel):
#     approved: bool
#     feedback: Optional[str] = None

# def critic_node(state: PaperState):
#     draft = state.get("draft_answer", "")
#     query = state["query"]
#     context = state.get("retrieved_context", "") + state.get("raw_data", "")
#     structured_llm = llm.with_structured_output(CriticOutput)
#     formatted = critic_prompt.format_messages(
#         query=query,
#         draft=draft,
#         sources_summary=context[:1000]
#     )
#     result = structured_llm.invoke(formatted)
#     if result.approved:
#         logger.info("--- Critic: Approved ---")
#         return {"final_answer": draft, "critique": None}
#     else:
#         logger.info(f"--- Critic: Rejected - {result.feedback[:100]} ---")
#         return {"critique": result.feedback, "revision_number": state.get("revision_number", 0) + 1}

import logging
from pydantic import BaseModel, Field
from typing import Literal, Optional
from langchain_core.messages import HumanMessage
from backend.core.llm import llm
# from backend.core import llm
from backend.ai.state import PaperState, TeamState
from backend.ai.prompts import (
    classifier_prompt, ask_paper_prompt, locate_paragraph_prompt,
    full_summary_prompt,
     web_merge_prompt, critic_prompt
)

from backend.core.retriever import retriever
from backend.ai.tools import _search_paper_raw
# استيراد الدوال الأساسية مباشرة
from backend.ai.tools import _search_paper as search_paper, _web_search as web_search, _get_paper_sections as get_paper_sections
from backend.ai.tools import _search_paper_raw

logger = logging.getLogger(__name__)

# ------------------- Classifier Node -------------------
class IntentClassification(BaseModel):
    intent: Literal["locate_paragraph", "full_summary", "ask_paper", "external_concept", "chat"]
    section: Optional[str] = Field(None, description="The section mentioned in the query, if any")
    page_hint: Optional[int] = Field(None, description="The page number mentioned, if any")

import json
import re

def _format_structured_draft(draft: str) -> str:
    """تحاول تحليل النص كـ JSON وإعادة تنسيقه إلى نص مقروء."""
    try:
        # محاولة استخراج JSON من النص (قد يكون محاطًا بنص آخر)
        json_match = re.search(r'\{.*\}', draft, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            # إذا احتوى على المفاتيح المحددة
            if "Main Thesis" in data and "Key Points" in data:
                parts = [f"**Main Thesis:** {data['Main Thesis']}"]
                if data.get("Key Points"):
                    parts.append("**Key Points:**")
                    for point in data["Key Points"]:
                        parts.append(f"- {point}")
                if data.get("Connections"):
                    parts.append(f"**Connections:** {data['Connections']}")
                return "\n\n".join(parts)
    except:
        pass
    return draft  # إذا فشل التحليل، يُرجع النص كما هو
def classifier_node(state: TeamState):
     # إذا كانت هناك نية مجبرة (من الواجهة)، استخدمها فوراً
    forced = state.get("forced_intent")
    if forced:
        logger.info(f"🚀 Forced intent: {forced} (by user filter selection)")
        print(f"\n🚀 [Classifier] forced intent = {forced}")
        return {
            "next_step": forced,
            "section_filter": state.get("section_filter"),
            "page_hint": state.get("page_hint")
        }
    messages = state.get("messages", [])
    if not messages:
        return {"next_step": "chat"}

    last_msg = messages[-1]
    content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

    # structured_llm = llm.with_structured_output(IntentClassification)
    # formatted = classifier_prompt.format_messages(input=content)
    structured_llm = llm.with_structured_output(IntentClassification)
    # تمرير تاريخ المحادثة كاملًا
    formatted = classifier_prompt.format_messages(
        messages="\n".join([m.content for m in messages[:-1]]),
        input=content
    )
    result = structured_llm.invoke(formatted)

    logger.info(f"Classifier from query: intent={result.intent}, section={result.section}, page={result.page_hint}")

    # **الأولوية للاختيار اليدوي إن وجد في الحالة**
    manual_section = state.get("section_filter")
    manual_page = state.get("page_hint")

    final_section = manual_section if manual_section is not None else result.section
    final_page = manual_page if manual_page is not None else result.page_hint

    logger.info(f"Final filter: section={final_section}, page={final_page}")
    print(f"\n🔍 [Classifier] intent = {result.intent}")
    print(f"   section (from query) = {result.section}, page_hint = {result.page_hint}")
    print(f"   manual section = {manual_section}, manual page = {manual_page}")
    print(f"   FINAL section = {final_section}, page = {final_page}\n")
    print(f"\n🔙 [Classifier] سيعيد: next_step='{result.intent}', section_filter='{final_section}', page_hint='{final_page}'")
    if not state.get("paper_loaded") and result.intent != "chat":
        return {
            "next_step": "chat",
            "messages": [HumanMessage(content="Please upload a paper first.")]
        }

    return {
        "next_step": result.intent,
        "section_filter": final_section,
        "page_hint": final_page
    }

# ------------------- Chatbot Node -------------------
def chatbot_node(state: TeamState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ------------------- Paper QA Agent (RAG) -------------------
# def ask_paper_node(state: PaperState):
#     logger.info(f"--- Paper QA: answering question ---")
#     query = state["query"]
#     # section = state.get("section_filter")
#     # page = state.get("page_hint")

#     context = search_paper(query, section_filter=None, page_hint=None)
#     if not context:
#         print("❌ [ask_paper] لم يتم العثور على سياق")
#     else:
#         print(f"✅ [ask_paper] سياق مسترجع: {len(context)} حرف")
#     formatted = ask_paper_prompt.format_messages(context=context, query=query)
#     response = llm.invoke(formatted)
#     print(f"\n📄 [ask_paper] question: {query}")
#     # print(f"   section_filter = {section}, page_hint = {page}")
#     return {"draft_answer": response.content, "retrieved_context": context}
def ask_paper_node(state: PaperState):
    print("\n📄📄📄 [ask_paper_node] تم استدعاء الوكيل 📄📄📄")
    logger.info(f"--- Paper QA: answering question ---")
    query = state["query"]
    context = search_paper(query, section_filter=None, page_hint=None)
    if not context:
        print("❌ [ask_paper] context فارغ!")
    else:
        print(f"📄 [ask_paper] context length = {len(context)}")
    formatted = ask_paper_prompt.format_messages(context=context, query=query)
    response = llm.invoke(formatted)
    draft = _format_structured_draft(response.content)
    print(f"\n📄 [ask_paper] question: {query}")
    return {"draft_answer": draft, "retrieved_context": context}
# ------------------- Locate Paragraph Node -------------------

from backend.ai.tools import _search_paper_raw, sort_chunks_by_chunk_id
from backend.core.retriever import retriever

def locate_paragraph_node(state: PaperState):
    logger.info(f"--- Locate Paragraph: finding specific paragraph ---")
    query = state["query"]
    section = state.get("section_filter")
    page = state.get("page_hint")
    
    # جلب النتائج الخام (بدون ترتيب)
    results = retriever.retrieve(query, top_k=15, section_filter=section, page_filter=page)
    
    # إعادة ترتيب حسب chunk_id
    sorted_docs, sorted_metas = sort_chunks_by_chunk_id(results)
    print("\n🔢 [Locate Paragraph] ترتيب القطع بعد الفرز بـ chunk_id:")
    for i, (doc, meta) in enumerate(zip(sorted_docs, sorted_metas)):
        chunk_id = meta.get("chunk_id", "?")
        preview = doc[:300].replace('\n', ' ')
        print(f"   {i+1}. chunk_id={chunk_id}, page={meta.get('page', '?')}, section='{meta.get('section', '?')}'")
        print(f"      {preview}...\n")
    # بناء السياق المرتب
    context = "\n\n".join([
        f"[Page {m.get('page', '?')} | {m.get('section', 'General')}]\n{t}"
        for t, m in zip(sorted_docs, sorted_metas)
    ]) if sorted_docs else "No relevant information found."
    
    formatted = locate_paragraph_prompt.format_messages(context=context, query=query)
    response = llm.invoke(formatted)
    draft = _format_structured_draft(response.content)
    print(f"\n🔎 [Locate Paragraph] question: {query}, page_hint = {page}, section_filter = {section}")
    return {"draft_answer": draft, "retrieved_context": context}
# def locate_paragraph_node(state: PaperState):
#     logger.info(f"--- Locate Paragraph: finding specific paragraph ---")
#     query = state["query"]
#     section = state.get("section_filter")   # ← أضف هذا
#     page = state.get("page_hint")
#     context = search_paper(query, section_filter=section, page_hint=page)
#     formatted = locate_paragraph_prompt.format_messages(context=context, query=query)
#     response = llm.invoke(formatted)
#     draft = _format_structured_draft(response.content)
#     print(f"\n🔎 [Locate Paragraph] question: {query}, page_hint = {page}, section_filter = {section}")
#     return {"draft_answer": draft, "retrieved_context": context}

# ------------------- Full Summary Node -------------------

def full_summary_node(state: PaperState):
    logger.info("--- Full Summary (Hierarchical) ---")
    logger.info("=== بدء التلخيص الهرمي ===")
    print("\n" + "="*50)
    print("📋 بدء التلخيص الهرمي للورقة")
    print("="*50)
    # sections_str = get_paper_sections.invoke({})
    sections_str = get_paper_sections()
    try:
        sections = sections_str.replace("Available sections: ", "").split(", ")
    except:
        sections = []
    print(f"📂 الأقسام المستخرجة: {sections}")
    # معالجة الأوراق بدون أقسام: تقسيم إلى كتل صفحات
    if not sections or sections == ["General"]:
        print("⚠️ لم يتم العثور على أقسام واضحة، سيتم تقسيم الورقة إلى مجموعات صفحات.")
        pages = retriever.get_available_pages()
        if not pages:
            sections = ["Whole Paper"]
        else:
            max_page = max(pages)
            sections = [f"Pages {start}-{min(start+2, max_page)}" for start in range(1, max_page+1, 3)]
            print(f"📄 تقسيم الصفحات إلى {len(sections)} مجموعات: {sections}")

    # المرحلة 1: ملخصات جزئية
    print("\n🔍 المرحلة 1: إنشاء ملخصات جزئية لكل قسم...")
    section_summaries = []
    for idx, sec in enumerate(sections, 1):     
        print(f"\n--- القسم {idx}/{len(sections)}: '{sec}' ---")
        # استخدام البحث بدون Rerank
        raw_context = _search_paper_raw(
            f"The main points, findings and conclusions of this section: {sec}",
            section_filter=sec if sec not in ["Whole Paper"] and not sec.startswith("Pages") else None
        )
        if not raw_context:
            print(f"⚠️ لا توجد نصوص مسترجعة للقسم '{sec}'، تخطي...")
            continue
        print(f"📄 تم استرجاع {len(raw_context)} حرف للقسم '{sec}'")
        partial_prompt = (
            f"Summarize the following section of a research paper in one concise paragraph (2-3 sentences). "
            f"Focus on key objectives, methods, results, or conclusions.\n\n"
            f"Section: {sec}\nContent:\n{raw_context}\n\nSummary:"
        )
        partial_response = llm.invoke(partial_prompt)
        
        partial_summary = partial_response.content
        print(f"📝 الملخص الجزئي لـ '{sec}':")
        print(partial_summary[:500] + ("..." if len(partial_summary) > 300 else ""))
        section_summaries.append(f"### {sec}\n{partial_response.content}")
        

    if not section_summaries:
        fallback_context = _search_paper_raw("summary of the whole paper", top_k=20)
        if fallback_context:
            section_summaries.append(f"### Overview\n{fallback_context}")

    combined_summaries = "\n\n".join(section_summaries)
    # استخدام قالب محسن إذا أردنا، لكن نستخدم كود مباشر هنا
    final_prompt = (
        "You are an expert at summarizing research papers. Below are summarized sections of a paper. "
        "Create a comprehensive, well‑structured final summary that includes:\n"
        "- Introduction and background\n"
        "- Methodology\n"
        "- Key findings and results\n"
        "- Discussion and implications\n"
        "- Conclusion\n\n"
        # f"User request: {query}\n\n" 
        # "Important: Strictly follow the user request above.\n\n" 
        f"Section summaries:\n{combined_summaries}\n\n"
        "Final Summary:"
    )
    final_response = llm.invoke(final_prompt)
    draft = _format_structured_draft(final_response)
    return {
        "draft_answer": draft,
        "retrieved_context": combined_summaries
    }

# ------------------- External Concept Node (Web) -------------------
def external_concept_node(state: PaperState):
    logger.info(f"--- External Concept: searching web ---")
    query = state["query"]
    web_data = web_search(query)
    paper_context = search_paper(query)
    formatted = web_merge_prompt.format_messages(
        paper_context=paper_context,
        web_data=web_data,
        query=query
    )
    response = llm.invoke(formatted)
    print(f"\n🌐 [External Concept] external question  : {query}")
    return {"draft_answer": response.content, "raw_data": web_data}

# ------------------- Critic Node -------------------
class CriticOutput(BaseModel):
    approved: bool
    feedback: Optional[str] = None

# def critic_node(state: PaperState):
#     draft = state.get("draft_answer", "")
#     query = state["query"]
#     context = state.get("retrieved_context", "") + state.get("raw_data", "")
#     structured_llm = llm.with_structured_output(CriticOutput)
#     formatted = critic_prompt.format_messages(
#         query=query,
#         draft=draft,
#         sources_summary=context[:1000]
#     )
def critic_node(state: PaperState):
    draft = state.get("draft_answer", "")
    query = state["query"]
    context = state.get("retrieved_context", "") + state.get("raw_data", "")
    structured_llm = llm.with_structured_output(CriticOutput)
    formatted = critic_prompt.format_messages(
        query=query,
        draft=draft,
        sources_summary=context[:1000]
    )
    result = structured_llm.invoke(formatted)
    if result.approved:
        logger.info("--- Critic: Approved ---")
        print("✅ [Critic] تمت الموافقة")
        return {"final_answer": draft, "critique": None}
    else:
        logger.info(f"--- Critic: Rejected - {result.feedback[:100] if result.feedback else 'No feedback'} ---")
        print(f"❌ [Critic] مرفوض: {result.feedback}")
        return {"critique": result.feedback, "revision_number": state.get("revision_number", 0) + 1}
    
    
    # result = structured_llm.invoke(formatted)
    # if result.approved:
    #     logger.info("--- Critic: Approved ---")
    #     print(f" [Critic] Approved: {result.feedback}")
    #     return {"final_answer": draft, "critique": None}
    # else:
    #     # logger.info(f"--- Critic: Rejected - {result.feedback[:100]} ---")
    #     logger.info(f"--- Critic: Rejected - {result.feedback[:100] if result.feedback else 'No feedback'} ---")
    #     print(f"❌ [Critic] Rejected: {result.feedback}")
    #     return {"critique": result.feedback, "revision_number": state.get("revision_number", 0) + 1}