import pymupdf4llm
import fitz
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument
import re
import pdfplumber
import os
from config import CHUNK_SIZE, CHUNK_OVERLAP,LLAMA_CLOUD_API_KEY
from backend.utils import (
    is_table_line,
    table_to_text,
    add_section_metadata,
    apply_overlap_to_chunks
)
# from liteparse import LiteParse

# def _load_with_liteparse(pdf_path: str) -> List[Document]:
#     print("⚡ جاري استخراج النص باستخدام LiteParse...")
    
#     from liteparse import LiteParse
#     parser = LiteParse()
#     result = parser.parse(pdf_path)
    
#     # LiteParse قد تُرجع النص في سمة markdown أو text
#     markdown_text = getattr(result, 'markdown', None) or getattr(result, 'text', '')
    
#     if not markdown_text or not markdown_text.strip():
#         # طباعة محتوى الكائن للمساعدة على التشخيص
#         print("⚠️ لم يتم العثور على نص. محتوى الكائن:")
#         print(dir(result))
#         print("العودة إلى PyMuPDF4LLM...")
#         return _load_with_pymupdf4llm(pdf_path)
    
#     print(f"📄 تم استخراج {len(markdown_text)} حرف باستخدام LiteParse")
#     print(f"   معاينة أول 300 حرف:\n{markdown_text[:50000]}...")
    
#     documents = [Document(page_content=markdown_text, metadata={"page": 1})]
#     return documents













# from marker.converters.pdf import PdfConverter
# from marker.models import create_model_dict
# from marker.config.parser import ConfigParser

# def _load_with_marker(pdf_path: str) -> List[Document]:
#     print("⚡ جاري استخراج النص باستخدام Marker...")
#     config_parser = ConfigParser()
#     converter = PdfConverter(
#         config=config_parser.generate_config_dict(),
#         artifact_dict=create_model_dict(),
#         processor_list=config_parser.get_processors(),
#         renderer=config_parser.get_renderer()
#     )
#     rendered = converter(pdf_path)
#     markdown_text = rendered.markdown

#     if not markdown_text.strip():
#         raise ValueError("أعادت Marker نصًا فارغًا")

    # Marker لا يُرجع صفحات منفصلة افتراضيًا، لذا نتعامل مع الناتج كمستند واحد.
    # لكن smart_chunking ستعالج المحتوى وتُضيف metadata لاحقًا.
    # للحصول على أرقام صفحات دقيقة، يمكننا استخدام rendered.blocks لكنه معقد.
    # نكتفي بصفحة واحدة الآن، حيث أن رقم الصفحة ليس ضروريًا لعملية الاسترجاع (يمكننا إضافته لاحقًا).
    # documents = [Document(page_content=markdown_text, metadata={"page": 1})]
    # print(f"✅ تم استخراج النص بنجاح باستخدام Marker (مستند واحد يحتوي كل الصفحات)")
    # return documents


# from typing import List
# from llama_cloud.client import LlamaCloud
# from llama_cloud.types import ParseOutputFormat

# ... (باقي الاستيرادات كما هي)

# import os
# from typing import List
# from langchain_core.documents import Document
# from llama_parse import LlamaParse


# def _load_with_llamaparse(pdf_path: str) -> List[Document]:
#     print("☁️  جاري استخراج النص باستخدام LlamaParse...")
    
#     parser = LlamaParse(
#         api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
#         result_type="markdown",
#         num_workers=4,
#         tier="premium",
#         # do_not_unroll_columns=True,  # <-- تعطيل فرد الأعمدة
#         # parsing_instructions="This document contains multi-column text and tables. Extract all text in correct reading order.",
#         verbose=False
#     )
    
#     # هذه الدالة تعيد قائمة من الكائنات
#     parsed_docs = parser.load_data(pdf_path)
    
#     if not parsed_docs:
#         raise ValueError("أعادت LlamaParse نتيجة فارغة")
    
#     documents = []
#     for i, doc in enumerate(parsed_docs):
#         if doc.text.strip():
#             print(f"\n📄 النص المستخرج من الصفحة {i+1}:\n{'='*40}")
#             print(doc.text)
#             print(f"{'='*40}\n")
#             documents.append(Document(
#                 page_content=doc.text,
#                 metadata={"page": i + 1}
#             ))
    
#     print(f"✅ تم استخراج {len(documents)} صفحة باستخدام LlamaParse")
#     return documents




def _load_with_pymupdf4llm(pdf_path: str) -> List[Document]:
    """الطريقة المحلية الافتراضية (الاحتياطية)."""
    pdf_document = fitz.open(pdf_path)
    documents = []
    for page_num in range(len(pdf_document)):
        try:
            page_md = pymupdf4llm.to_markdown(pdf_path, pages=[page_num])
        except TypeError:
            page = pdf_document[page_num]
            page_md = page.get_text()
        documents.append(Document(
            page_content=page_md,
            metadata={"page": page_num + 1}
        ))
    return documents

def load_pdf_as_documents(pdf_file):
    pdf_document = fitz.open(pdf_file)
    documents = []
    for page_num in range(len(pdf_document)):
        try:
            page_md = pymupdf4llm.to_markdown(pdf_file, pages=[page_num])
        except TypeError:
            page = pdf_document[page_num]
            page_md = page.get_text()
        documents.append(Document(text=page_md, metadata={"page": page_num + 1}))
    for i, doc in enumerate(documents[:8]):
        print(f"  ( text ):\n{doc.text}")    
    return documents


def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    print("Documents received:", len(documents))
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    all_chunks = []

    for doc in documents:
        page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
        # text = doc.text

        text = getattr(doc, 'text', None) or getattr(doc, 'page_content', '')
        lines = text.split('\n')
        current_paragraph = ""
        inside_table = False
        table_buffer = ""
        post_table = False          # <-- حالة جديدة: بعد انتهاء الجدول مباشرة

        for line in lines:
            # --- داخل جدول؟ ---
            if is_table_line(line):
                inside_table = True
                table_buffer += line + "\n"
                post_table = False
                continue

            # --- خرجنا الآن من جدول (أو سطر غير جدول أثناء post_table) ---
            if inside_table:
                # معالجة الجدول المُنتهي
                table_text = table_buffer.strip()
                structured_table = table_to_text(table_text)
                all_chunks.append({
                    "text": structured_table,
                    "page": page_num,
                    "type": "table"
                })
                table_buffer = ""
                inside_table = False
                post_table = True        # ننتظر تسمية محتملة

            # --- حالة ما بعد الجدول (نتجاوز الفراغات ونلتقط التسمية) ---
            if post_table:
                # إذا كان السطر فارغاً (أو مجرد فراغات) – تخطّه
                if not line.strip():
                    continue
                # هل هو تسمية؟
                if re.match(r'^(Table|table)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
                    # ألحق التسمية بالقطعة الأخيرة (التي هي الجدول)
                    caption = line.strip()
                    if all_chunks and all_chunks[-1]["type"] == "table":
                        all_chunks[-1]["text"] += "\n" + caption
                    post_table = False
                    continue
                else:
                    # ليس فراغاً ولا تسمية – إذن انتهت حالة ما بعد الجدول
                    post_table = False
                    # ولا نُعيد السطر؛ سنعالجه بشكل طبيعي في الأسفل

            # --- عنوان؟ ---
            is_heading = re.match(r'^\s*#{1,6}\s+', line)
            if is_heading:
                if current_paragraph.strip():
                    estimated_tokens = len(current_paragraph.split()) * 1.3
                    if estimated_tokens <= chunk_size:
                        all_chunks.append({
                            "text": current_paragraph.strip(),
                            "page": page_num
                        })
                    else:
                        temp_doc = LlamaDocument(
                            text=current_paragraph,
                            metadata={"page": page_num}
                        )
                        nodes = splitter.get_nodes_from_documents([temp_doc])
                        chunk_list = [{
                            "text": node.text,
                            "page": page_num
                        } for node in nodes]
                        if len(chunk_list) > 1:
                            chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
                        all_chunks.extend(chunk_list)
                current_paragraph = line
                continue

            # --- سطر عادي (يُضاف للفقرة الحالية) ---
            if current_paragraph:
                current_paragraph += "\n" + line
            else:
                current_paragraph = line

            estimated_tokens = len(current_paragraph.split()) * 1.3
            if estimated_tokens > chunk_size * 1.2:
                temp_doc = LlamaDocument(
                    text=current_paragraph,
                    metadata={"page": page_num}
                )
                nodes = splitter.get_nodes_from_documents([temp_doc])
                chunk_list = [{
                    "text": node.text,
                    "page": page_num
                } for node in nodes]
                if len(chunk_list) > 1:
                    chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
                all_chunks.extend(chunk_list)
                current_paragraph = ""

        # نهاية الصفحة: إذا بقي جدول غير معالج (حدث نادر)
        if inside_table and table_buffer.strip():
            structured_table = table_to_text(table_buffer)
            all_chunks.append({
                "text": structured_table,
                "page": page_num,
                "type": "table"
            })

        # الفقرة المتبقية
        if current_paragraph.strip():
            estimated_tokens = len(current_paragraph.split()) * 1.3
            if estimated_tokens <= chunk_size* 1.2:
                all_chunks.append({
                    "text": current_paragraph.strip(),
                    "page": page_num
                })
            else:
                temp_doc = LlamaDocument(
                    text=current_paragraph,
                    metadata={"page": page_num}
                )
                nodes = splitter.get_nodes_from_documents([temp_doc])
                chunk_list = [{
                    "text": node.text,
                    "page": page_num
                } for node in nodes]
                if len(chunk_list) > 1:
                    chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
                all_chunks.extend(chunk_list)

    return all_chunks
    # هي كنت عندا اخر شي 


def process_paper(pdf_path: str):
    """الوظيفة الكاملة لمعالجة الورقة وإرجاع القطع مع البيانات الوصفية"""
    documents = load_pdf_as_documents(pdf_path)
    # documents = _load_with_llamaparse(pdf_path)
    # documents = _load_with_marker(pdf_path)
    # documents = _load_with_liteparse(pdf_path)
    


    chunks = smart_chunking(documents)
    chunks = add_section_metadata(chunks)
    print("\n" + "="*60)
    print(f"📦 إجمالي القطع النهائية (بعد المعالجة الكاملة): {len(chunks)}")
    print("="*60)
    for i, c in enumerate(chunks[:30 ]):  # يمكنك زيادة العدد أو استخدام len(chunks)
        print("="*40)
        print(f"CHUNK {i}")
        print(f"  page: {c.get('page')}")
        print(f"  section: {c.get('section')}")
        print(f"  type: {c.get('type', 'paragraph')}")
        print(f"  text length: {len(c['text'])}")
        print(f"  text preview: {c}...")
    print("="*60 + "\n")
    return chunks
