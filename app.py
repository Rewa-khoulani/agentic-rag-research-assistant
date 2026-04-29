
import streamlit as st
import tempfile
import os
import traceback

# =========================
# Page Config + Styling
# =========================
st.set_page_config(page_title="AI Paper Assistant", layout="wide")

st.markdown("""
<style>
.main-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 10px;
}
.subtitle {
    color: #6c757d;
    margin-bottom: 25px;
}
.sidebar-title {
    font-size: 18px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📚 AI Research Paper Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions and explore research papers intelligently using RAG</div>', unsafe_allow_html=True)

# =========================
# Session State Init
# =========================
if "paper_processed" not in st.session_state:
    st.session_state.paper_processed = False
if "sections" not in st.session_state:
    st.session_state.sections = []
if "pages" not in st.session_state:
    st.session_state.pages = []
if "collection_name" not in st.session_state:
    st.session_state.collection_name = "papers"
if "section_filter" not in st.session_state:
    st.session_state.section_filter = None
if "page_filter" not in st.session_state:
    st.session_state.page_filter = None
if "messages" not in st.session_state:
    st.session_state.messages = []



# هدول جداد 
if "section_selector" not in st.session_state:
    st.session_state.section_selector = "All Sections"
if "page_selector" not in st.session_state:
    st.session_state.page_selector = "All Pages"
# =========================
# Backend Loading
# =========================
with st.spinner("Loading models and dependencies..."):
    try:
        from backend.processor import process_paper
        from backend.core.retriever import retriever
        from backend.ai.graphs import master_graph
        from langchain_core.messages import HumanMessage
        st.success("✅ Models loaded successfully")
    except Exception as e:
        st.error(f"❌ Failed to load backend components:\n\n```\n{traceback.format_exc()}\n```")
        st.stop()

# =========================
# Sidebar
# =========================
# with st.sidebar:
#     st.markdown('<div class="sidebar-title">📂 Upload Paper</div>', unsafe_allow_html=True)
#     uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

#     if uploaded_file and not st.session_state.paper_processed:
#         with st.spinner("Processing paper..."):
#             try:
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#                     tmp.write(uploaded_file.getvalue())
#                     tmp_path = tmp.name

#                 chunks = process_paper(tmp_path)
#                 collection = retriever.create_collection(chunks, st.session_state.collection_name)
#                 sections = retriever.get_available_sections()
#                 pages = retriever.get_available_pages()

#                 st.session_state.paper_processed = True
#                 st.session_state.sections = sections
#                 st.session_state.pages = pages

#                 os.unlink(tmp_path)
#                 st.success("Paper processed successfully!")
#             except Exception as e:
#                 st.error(f"❌ Error processing paper:\n\n```\n{traceback.format_exc()}\n```")
#                 st.stop()

#     if st.session_state.paper_processed:
#         st.markdown("---")
#         st.markdown('<div class="sidebar-title">🔍 Advanced Filters</div>', unsafe_allow_html=True)

#         selected_section = st.selectbox(
#             "Select section (optional)",
#             ["All Sections"] + st.session_state.sections
#         )
#         selected_page = st.selectbox(
#             "Select page (optional)",
#             ["All Pages"] + [str(p) for p in st.session_state.pages]
#         )

#         section_filter = None if selected_section == "All Sections" else selected_section
#         page_filter = None if selected_page == "All Pages" else int(selected_page)

#         st.session_state.section_filter = section_filter
#         st.session_state.page_filter = page_filter

#         st.markdown("---")

#         if st.button("Reset Paper"):
#             st.session_state.paper_processed = False
#             st.session_state.sections = []
#             st.session_state.pages = []
#             st.session_state.section_filter = None
#             st.session_state.page_filter = None
#             st.session_state.messages = []
#             st.rerun()
# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown('<div class="sidebar-title">📂 Upload Paper</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file and not st.session_state.paper_processed:
        with st.spinner("Processing paper..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                chunks = process_paper(tmp_path)
                collection = retriever.create_collection(chunks, st.session_state.collection_name)
                sections = retriever.get_available_sections()
                pages = retriever.get_available_pages()

                st.session_state.paper_processed = True
                st.session_state.sections = sections
                st.session_state.pages = pages

                os.unlink(tmp_path)
                st.success("Paper processed successfully!")
            except Exception as e:
                st.error(f"❌ Error processing paper:\n\n```\n{traceback.format_exc()}\n```")
                st.stop()

#     if st.session_state.paper_processed:
#         st.markdown("---")
#         st.markdown('<div class="sidebar-title">🔍 Advanced Filters</div>', unsafe_allow_html=True)

#         # ---- دوال التحكم لجعل الاختيار حصريًا ----
#         def on_section_change():
#             if st.session_state.section_selector != "All Sections":
#                 st.session_state.page_selector = "All Pages"

#         def on_page_change():
#             if st.session_state.page_selector != "All Pages":
#                 st.session_state.section_selector = "All Sections"

#         selected_section = st.selectbox(
#             "Select section (optional)",
#             ["All Sections"] + st.session_state.sections,
#             key="section_selector",
#             on_change=on_section_change
#         )
#         selected_page = st.selectbox(
#             "Select page (optional)",
#             ["All Pages"] + [str(p) for p in st.session_state.pages],
#             key="page_selector",
#             on_change=on_page_change
#         )

#         section_filter = None if selected_section == "All Sections" else selected_section
#         page_filter = None if selected_page == "All Pages" else int(selected_page)

#         st.session_state.section_filter = section_filter
#         st.session_state.page_filter = page_filter

#         st.markdown("---")

#         if st.button("Reset Paper"):
#             st.session_state.paper_processed = False
#             st.session_state.sections = []
#             st.session_state.pages = []
#             st.session_state.section_filter = None
#             st.session_state.page_filter = None
#             st.session_state.section_selector = "All Sections"
#             st.session_state.page_selector = "All Pages"
#             st.session_state.messages = []
#             st.rerun()
    if st.session_state.paper_processed:
        st.markdown("---")
        st.markdown('<div class="sidebar-title">🔍 Advanced Filters</div>', unsafe_allow_html=True)

        # --- دوال حصرية مع تعطيل الحقل الآخر ---
        def on_section_change():
            if st.session_state.section_selector != "All Sections":
                st.session_state.page_selector = "All Pages"

        def on_page_change():
            if st.session_state.page_selector != "All Pages":
                st.session_state.section_selector = "All Sections"

        # تحديد حالة التعطيل
        section_disabled = st.session_state.page_selector != "All Pages"
        page_disabled = st.session_state.section_selector != "All Sections"

        selected_section = st.selectbox(
            "Select section (optional)",
            ["All Sections"] + st.session_state.sections,
            key="section_selector",
            on_change=on_section_change,
            disabled=section_disabled
        )
        selected_page = st.selectbox(
            "Select page (optional)",
            ["All Pages"] + [str(p) for p in st.session_state.pages],
            key="page_selector",
            on_change=on_page_change,
            disabled=page_disabled
        )

        section_filter = None if selected_section == "All Sections" else selected_section
        page_filter = None if selected_page == "All Pages" else int(selected_page)

        st.session_state.section_filter = section_filter
        st.session_state.page_filter = page_filter

        st.markdown("---")

        if st.button("Reset Paper"):
            st.session_state.paper_processed = False
            st.session_state.sections = []
            st.session_state.pages = []
            st.session_state.section_filter = None
            st.session_state.page_filter = None
            st.session_state.section_selector = "All Sections"
            st.session_state.page_selector = "All Pages"
            st.session_state.messages = []
            st.rerun()
# =========================
# Chat Area
# =========================
if st.session_state.paper_processed:
    st.markdown("### 💬 Ask Questions About the Paper")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your question here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing and retrieving answer..."):
                try:
                    input_state = {
                        "messages": [HumanMessage(content=prompt)],
                        "paper_loaded": True,
                        "section_filter": st.session_state.section_filter,
                        "page_hint": st.session_state.page_filter
                        
                    }
                    
                    config = {"configurable": {"thread_id": "session1"}}
                    if st.session_state.section_filter or st.session_state.page_filter:
                        input_state["forced_intent"] = "locate_paragraph"
                    result = master_graph.invoke(input_state, config)

                    answer = result.get("final_response", "Sorry, I could not generate an answer.")
                    st.markdown(answer)

                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"❌ Error generating answer:\n\n```\n{traceback.format_exc()}\n```")

else:
    st.info("👈 Please upload a research paper (PDF) from the sidebar to begin.")