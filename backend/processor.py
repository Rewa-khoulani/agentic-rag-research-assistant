import pymupdf4llm
import fitz
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument
import re
import pdfplumber
import os
from config import LLAMA_CLOUD_API_KEY
# CHUNK_SIZE, 
# CHUNK_OVERLAP,

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

import re

MAX_CHARS = 1500  # تستطيع تغييره

def split_text_into_sentences(text: str) -> list:
    """
    تقسيم النص إلى جمل باستخدام تعبير بسيط.
    يمكنك استبدالها بـ nltk.sent_tokenize إذا كانت مثبتة.
    """
    # هذا النمط يلتقط نهاية الجملة: نقطة، علامة استفهام، تعجب متبوعة بفراغ أو نهاية النص
    # لكنه ليس مثالياً 100%، يمكن تحسينه أو استخدام nltk
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # ازالة الفراغات الزائدة وإعادة الجمل الفارغة
    return [s.strip() for s in sentences if s.strip()]

def chunk_by_sentences_with_char_limit(text: str, max_chars: int) -> list:
    """
    يدمج الجمل إلى قطع بحيث لا تتجاوز كل قطعة max_chars أحرفاً.
    """
    sentences = split_text_into_sentences(text)
    chunks = []
    current_chunk = ""

    for sent in sentences:
        # إذا كانت الجملة الحالية لوحدها أطول من max_chars (نادر جداً) نقبلها كما هي
        if len(sent) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            chunks.append(sent.strip())
            continue

        # هل إضافة الجملة ستتجاوز الحد؟
        if current_chunk:
            candidate = current_chunk + " " + sent
        else:
            candidate = sent

        if len(candidate) > max_chars:
            # نغلق القطعة الحالية ونبدأ بجملة جديدة
            chunks.append(current_chunk.strip())
            current_chunk = sent
        else:
            current_chunk = candidate

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
CHUNK_SIZE = 200        # tokens per chunk
CHUNK_OVERLAP = 20      # overlap only within a split section
from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
import re
from typing import List, Dict, Any
def clean_margin_text(text: str) -> str:
    # يحذف أي سطر يبدأ بـ > (اقتباس أو هامش)
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if not line.strip().startswith('>')]
    # يمكن إضافة أنماط أخرى حسب الحاجة
    return '\n'.join(cleaned_lines)
import re

def clean_chunk_text(text: str) -> str:
    """
    يزيل رموز Markdown الشائعة من النص:
    - ###، ##، #
    - **نص**، *نص*
    - [نص](رابط)
    - > من بداية السطر
    """
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    return text.strip()
def flush_section_to_chunks(text_buffer, pages_set, current_heading, splitter, all_chunks):
    """
    تُقطع النص المتراكم عبر SentenceSplitter وتُنظّف القطع الناتجة.
    """
    if not text_buffer.strip():
        return

    temp_doc = LlamaDocument(text=text_buffer)
    nodes = splitter.get_nodes_from_documents([temp_doc])

    pages_list = sorted(list(pages_set))
    if not pages_list:
        page_meta = "Unknown"
    elif len(pages_list) > 1:
        page_meta = f"{pages_list[0]}-{pages_list[-1]}"
    else:
        page_meta = str(pages_list[0])

    for node in nodes:
        # cleaned_text = clean_chunk_text(node.text)   # <-- التنظيف هنا
        all_chunks.append({
            "text": node.text,
            "page": page_meta,
            "type": "text",
            "heading": current_heading
        })

# def flush_section_to_chunks(text_buffer: str, pages_set: set, current_heading: str, splitter: SentenceSplitter, all_chunks: list):
#     """
#     Helper function to process accumulated text through the SentenceSplitter.
#     It clears the buffer and assigns multi-page and heading metadata.
#     """
#     if not text_buffer.strip():
#         return
    
#     # Let LlamaIndex handle the chunk size, sentence boundaries, and overlap natively
#     temp_doc = LlamaDocument(text=text_buffer)
#     nodes = splitter.get_nodes_from_documents([temp_doc])
    
#     # Format pages nicely (e.g., "5" or "5-6" if the section spans page breaks)
#     pages_list = sorted(list(pages_set))
#     if not pages_list:
#         page_meta = "Unknown"
#     elif len(pages_list) > 1:
#         page_meta = f"{pages_list[0]}-{pages_list[-1]}"
#     else:
#         page_meta = str(pages_list[0])
    
#     for node in nodes:
#         all_chunks.append({
#             "text": node.text,
#             "page": page_meta,
#             "type": "text",
#             "heading": current_heading
#         })
def smart_chunking(documents, chunk_size=230, chunk_overlap=50):
    """
    تقطيع ذكي للأوراق البحثية يحترم الأقسام والجداول،
    مع تنظيف Markdown وإزالة قسم المراجع.
    """
    print("Documents received:", len(documents))

    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    all_chunks = []

    # متغيرات الحالة عبر الصفحات
    current_paragraph = ""
    current_pages = set()
    current_heading = "Introduction"

    inside_table = False
    table_buffer = ""
    table_pages = set()
    post_table = False

    for doc in documents:
        page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
        text = getattr(doc, 'text', None) or getattr(doc, 'page_content', '')
        text = clean_margin_text(text)          # إزالة علامات > من بداية السطور
        lines = text.split('\n')

        for line in lines:
            # 1. التعامل مع دخول الجدول
            if is_table_line(line):
                if not inside_table:
                    flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)
                    current_paragraph = ""
                    current_pages.clear()
                inside_table = True
                table_buffer += line + "\n"
                table_pages.add(page_num)
                post_table = False
                continue

            # 2. خروج من الجدول
            if inside_table:
                structured_table = table_to_text(table_buffer.strip())
                t_pages = sorted(list(table_pages))
                t_page_meta = f"{t_pages[0]}-{t_pages[-1]}" if len(t_pages) > 1 else str(t_pages[0])
                all_chunks.append({
                    "text": structured_table,
                    "page": t_page_meta,
                    "type": "table",
                    "heading": current_heading
                })
                table_buffer = ""
                table_pages.clear()
                inside_table = False
                post_table = True

            # 3. تعليق الجدول
            if post_table:
                if not line.strip():
                    continue
                if re.match(r'^(Table|table|Figure|figure)\s*[\dIVX]+[:.-]', line, re.IGNORECASE):
                    if all_chunks and all_chunks[-1]["type"] == "table":
                        all_chunks[-1]["text"] += "\n\nCaption: " + line.strip()
                    post_table = False
                    continue
                else:
                    post_table = False

            # 4. العناوين
            is_heading = re.match(r'^\s*#{1,6}\s+', line)
            if is_heading:
                flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)

                # استخراج عنوان نظيف (بدون نجوم و #)
                raw = line.strip().lstrip('#').strip()
                current_heading = re.sub(r'\*+', '', raw).strip()   # إزالة ** إن وجدت

                current_paragraph = line + "\n"
                current_pages = {page_num}
                continue

            # 5. نص عادي
            if line.strip():
                current_paragraph += line + "\n"
                current_pages.add(page_num)

    # 6. تصريف البقايا في النهاية
    if inside_table and table_buffer.strip():
        structured_table = table_to_text(table_buffer.strip())
        t_pages = sorted(list(table_pages))
        t_page_meta = f"{t_pages[0]}-{t_pages[-1]}" if len(t_pages) > 1 else str(t_pages[0])
        all_chunks.append({
            "text": structured_table,
            "page": t_page_meta,
            "type": "table",
            "heading": current_heading
        })

    flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)

    # 7. فلترة قسم المراجع (اختياري، يمكن الاستغناء عنه لو أضفنا حالة تجاهل)
    all_chunks = [c for c in all_chunks if not re.match(
        r'^(References?|Bibliography|Works\s*Cited)\s*$',
        c.get("heading", ""),
        re.IGNORECASE
    )]

    return all_chunks
# def smart_chunking(documents, chunk_size=230, chunk_overlap=50):
#     print("Documents received:", len(documents))
    
#     # Initialize the LlamaIndex splitter
#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
    
#     all_chunks = []
    
#     # State variables that persist ACROSS pages
#     current_paragraph = ""
#     current_pages = set()
#     current_heading = "Introduction"
    
#     # Table state variables
#     inside_table = False
#     table_buffer = ""
#     table_pages = set()
#     post_table = False 
    
#     for doc in documents:
#         page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
#         text = getattr(doc, 'text', None) or getattr(doc, 'page_content', '')
#         text = clean_margin_text(text)
#            # <--- أضف هذا السطر
#         lines = text.split('\n')
        
#         for line in lines:
#             # 1. Handle Tables (Entering and processing)
#             if is_table_line(line):
#                 if not inside_table:
#                     # Flush the accumulated text BEFORE the table starts
#                     flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)
#                     current_paragraph = ""
#                     current_pages.clear()
                
#                 inside_table = True
#                 table_buffer += line + "\n"
#                 table_pages.add(page_num)
#                 post_table = False
#                 continue

#             # 2. Exiting a Table
#             if inside_table:
#                 # We hit a non-table line. Process the finished table.
#                 structured_table = table_to_text(table_buffer.strip())
                
#                 # Format table page metadata
#                 t_pages = sorted(list(table_pages))
#                 t_page_meta = f"{t_pages[0]}-{t_pages[-1]}" if len(t_pages) > 1 else str(t_pages[0])
                
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": t_page_meta,
#                     "type": "table",
#                     "heading": current_heading
#                 })
                
#                 # Reset table state
#                 table_buffer = ""
#                 table_pages.clear()
#                 inside_table = False
#                 post_table = True

#             # 3. Handle Captions Below the Table
#             if post_table:
#                 # Skip any blank lines immediately following the table
#                 if not line.strip():
#                     continue
                
#                 # Check if the first text we see is a caption
#                 if re.match(r'^(Table|table|Figure|figure)\s*[\dIVX]+[:.-]', line, re.IGNORECASE):
#                     if all_chunks and all_chunks[-1]["type"] == "table":
#                         all_chunks[-1]["text"] += "\n\nCaption: " + line.strip()
#                     post_table = False
#                     continue
#                 else:
#                     # It's not a caption, meaning the table section is truly over
#                     post_table = False
#                     # We do NOT 'continue' here, so the line gets processed as normal text below

#             # 4. Handle Headings
#             is_heading = re.match(r'^\s*#{1,6}\s+', line)
#             if is_heading:
#                 # Flush the current section under the old heading
#                 flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)
                
#                 # Start new section
#                 current_heading = line.strip().lstrip('#').strip()
#                 current_paragraph = line + "\n"
#                 current_pages = {page_num}
#                 continue

#             # 5. Accumulate Normal Text
#             if line.strip(): 
#                 current_paragraph += line + "\n"
#                 current_pages.add(page_num)

#     # 6. End of ALL documents: flush remaining text and tables
#     if inside_table and table_buffer.strip():
#         structured_table = table_to_text(table_buffer.strip())
#         t_pages = sorted(list(table_pages))
#         t_page_meta = f"{t_pages[0]}-{t_pages[-1]}" if len(t_pages) > 1 else str(t_pages[0])
#         all_chunks.append({
#             "text": structured_table,
#             "page": t_page_meta,
#             "type": "table",
#             "heading": current_heading
#         })
        
#     flush_section_to_chunks(current_paragraph, current_pages, current_heading, splitter, all_chunks)
#     # بعد نهاية معالجة كل المستندات:
#     all_chunks = [c for c in all_chunks if not re.match(r'^(References)',
#                                                      c.get("heading", ""), re.IGNORECASE)]
#     return all_chunks

# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
#     print("Documents received:", len(documents))

#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=0  # we handle overlap manually, only when needed
#     )

#     all_chunks = []

#     for doc in documents:
#         page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
#         text = getattr(doc, 'text', None) or getattr(doc, 'page_content', '')

#         lines = text.split('\n')

#         # Each section is {"heading": str, "lines": [...], "page": int}
#         sections = []
#         current_section = {"heading": None, "lines": [], "page": page_num}

#         # ── Pass 1: split text into sections by heading ──────────────────────
#         for line in lines:
#             if re.match(r'^\s*#{1,6}\s+', line):
#                 if current_section["lines"] or current_section["heading"]:
#                     sections.append(current_section)
#                 current_section = {"heading": line.strip(), "lines": [], "page": page_num}
#             else:
#                 current_section["lines"].append(line)

#         if current_section["lines"] or current_section["heading"]:
#             sections.append(current_section)

#         # ── Pass 2: process each section ─────────────────────────────────────
#         for section in sections:
#             heading = section["heading"] or ""
#             page = section["page"]
#             body_lines = section["lines"]

#             # ── handle tables inside the section ─────────────────────────────
#             table_buffer = ""
#             inside_table = False
#             post_table = False
#             text_lines = []   # non-table lines collected for paragraph text

#             for line in body_lines:
#                 if is_table_line(line):
#                     inside_table = True
#                     table_buffer += line + "\n"
#                     post_table = False
#                     continue

#                 if inside_table:
#                     structured_table = table_to_text(table_buffer.strip())
#                     all_chunks.append({
#                         "text": structured_table,
#                         "page": page,
#                         "section": heading,
#                         "type": "table"
#                     })
#                     table_buffer = ""
#                     inside_table = False
#                     post_table = True

#                 if post_table:
#                     if not line.strip():
#                         continue
#                     if re.match(r'^(Table|table)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
#                         if all_chunks and all_chunks[-1]["type"] == "table":
#                             all_chunks[-1]["text"] += "\n" + line.strip()
#                         post_table = False
#                         continue
#                     else:
#                         post_table = False

#                 text_lines.append(line)

#             # flush any trailing table
#             if inside_table and table_buffer.strip():
#                 structured_table = table_to_text(table_buffer.strip())
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page,
#                     "section": heading,
#                     "type": "table"
#                 })

#             # ── split paragraph text ──────────────────────────────────────────
#             paragraph = "\n".join(text_lines).strip()
#             if not paragraph:
#                 continue

#             # prepend heading to the paragraph so the splitter sees it
#             full_text = (heading + "\n" + paragraph).strip() if heading else paragraph

#             estimated_tokens = len(full_text.split()) * 1.3

#             if estimated_tokens <= chunk_size:
#                 # fits in one chunk — no overlap needed
#                 all_chunks.append({
#                     "text": full_text,
#                     "page": page,
#                     "section": heading,
#                     "type": "paragraph"
#                 })
#             else:
#                 # needs splitting — apply overlap only within this section
#                 temp_doc = LlamaDocument(
#                     text=full_text,
#                     metadata={"page": page}
#                 )
#                 nodes = splitter.get_nodes_from_documents([temp_doc])
#                 chunk_list = [
#                     {"text": node.text, "page": page, "section": heading, "type": "paragraph"}
#                     for node in nodes
#                 ]
#                 if len(chunk_list) > 1:
#                     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=overlap_size_from_tokens(chunk_overlap, chunk_list))
#                 all_chunks.extend(chunk_list)

#     return all_chunks


# def overlap_size_from_tokens(token_overlap: int, chunks: list) -> int:
#     """
#     Converts a token-based overlap target into a line count for apply_overlap_to_chunks.
#     Estimates how many lines correspond to `token_overlap` tokens based on average line length.
#     """
#     if not chunks:
#         return 2
#     total_lines = sum(len(c["text"].split("\n")) for c in chunks)
#     total_tokens = sum(len(c["text"].split()) * 1.3 for c in chunks)
#     if total_tokens == 0:
#         return 2
#     lines_per_token = total_lines / total_tokens
#     return max(1, round(token_overlap * lines_per_token))
# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
#     print("Documents received:", len(documents))
#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     all_chunks = []

#     for doc in documents:
#         page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
#         # text = doc.text

#         text = getattr(doc, 'text', None) or getattr(doc, 'page_content', '')
#         lines = text.split('\n')
#         current_paragraph = ""
#         inside_table = False
#         table_buffer = ""
#         post_table = False          # <-- حالة جديدة: بعد انتهاء الجدول مباشرة

#         for line in lines:
#             # --- داخل جدول؟ ---
#             if is_table_line(line):
#                 inside_table = True
#                 table_buffer += line + "\n"
#                 post_table = False
#                 continue

#             # --- خرجنا الآن من جدول (أو سطر غير جدول أثناء post_table) ---
#             if inside_table:
#                 # معالجة الجدول المُنتهي
#                 table_text = table_buffer.strip()
#                 structured_table = table_to_text(table_text)
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page_num,
#                     "type": "table"
#                 })
#                 table_buffer = ""
#                 inside_table = False
#                 post_table = True        # ننتظر تسمية محتملة

#             # --- حالة ما بعد الجدول (نتجاوز الفراغات ونلتقط التسمية) ---
#             if post_table:
#                 # إذا كان السطر فارغاً (أو مجرد فراغات) – تخطّه
#                 if not line.strip():
#                     continue
#                 # هل هو تسمية؟
#                 if re.match(r'^(Table|table)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
#                     # ألحق التسمية بالقطعة الأخيرة (التي هي الجدول)
#                     caption = line.strip()
#                     if all_chunks and all_chunks[-1]["type"] == "table":
#                         all_chunks[-1]["text"] += "\n" + caption
#                     post_table = False
#                     continue
#                 else:
#                     # ليس فراغاً ولا تسمية – إذن انتهت حالة ما بعد الجدول
#                     post_table = False
#                     # ولا نُعيد السطر؛ سنعالجه بشكل طبيعي في الأسفل

#             # --- عنوان؟ ---
#             is_heading = re.match(r'^\s*#{1,6}\s+', line)
#             if is_heading:
#                 if current_paragraph.strip():
#                     estimated_tokens = len(current_paragraph.split()) * 1.3
#                     if estimated_tokens <= chunk_size:
#                         all_chunks.append({
#                             "text": current_paragraph.strip(),
#                             "page": page_num
#                         })
#                     else:
#                         temp_doc = LlamaDocument(
#                             text=current_paragraph,
#                             metadata={"page": page_num}
#                         )
#                         nodes = splitter.get_nodes_from_documents([temp_doc])
#                         chunk_list = [{
#                             "text": node.text,
#                             "page": page_num
#                         } for node in nodes]
#                         if len(chunk_list) > 1:
#                             chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
#                         all_chunks.extend(chunk_list)
#                 current_paragraph = line
#                 continue
#             MAX_CHARS = 1500 
#             # --- سطر عادي (يُضاف للفقرة الحالية) ---
#             if current_paragraph:
#                 current_paragraph += "\n" + line
#             else:
#                 current_paragraph = line

#             # estimated_tokens = len(current_paragraph.split()) * 1.3
#             if len(current_paragraph) >= MAX_CHARS:
#             # if estimated_tokens > chunk_size * 1.2:
#                 # temp_doc = LlamaDocument(
#                 #     text=current_paragraph,
#                 #     metadata={"page": page_num}
#                 # )
#                 # nodes = splitter.get_nodes_from_documents([temp_doc])
#                 # chunk_list = [{
#                 #     "text": node.text,
#                 #     "page": page_num
#                 # } for node in nodes]
#                 # if len(chunk_list) > 1:
#                 #     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
#                 # all_chunks.extend(chunk_list)
#                 # current_paragraph = ""
#                 sub_chunks = chunk_by_sentences_with_char_limit(current_paragraph, MAX_CHARS)
#                 for chk in sub_chunks:
#                      all_chunks.append({
#                         "text": chk,
#                         "page": page_num,
#                         "type": "paragraph"
#                      })
#                 current_paragraph = "" 

#         # نهاية الصفحة: إذا بقي جدول غير معالج (حدث نادر)
#         if inside_table and table_buffer.strip():
#             structured_table = table_to_text(table_buffer)
#             all_chunks.append({
#                 "text": structured_table,
#                 "page": page_num,
#                 "type": "table"
#             })

#         # الفقرة المتبقية
#         # if current_paragraph.strip():
#         if current_paragraph.strip():
#             temp_doc = LlamaDocument(
#                 text=current_paragraph,
#                 metadata={"page": page_num}
#             )
#             nodes = splitter.get_nodes_from_documents([temp_doc])
#             chunk_list = [{"text": node.text, "page": page_num} for node in nodes]
#             if len(chunk_list) > 1:
#                 chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
#             all_chunks.extend(chunk_list)
#             # estimated_tokens = len(current_paragraph.split()) * 1.3
#             # if estimated_tokens <= chunk_size* 1.2:
#             # if len(current_paragraph) >= MAX_CHARS:
#             #     sub_chunks = chunk_by_sentences_with_char_limit(current_paragraph, MAX_CHARS)
#             #     for chk in sub_chunks:
#             #         all_chunks.append({
#             #             "text": chk,
#             #             "page": page_num,
#             #             "type": "paragraph"
#             #         })

#                 # all_chunks.append({
#                 #     "text": current_paragraph.strip(),
#                 #     "page": page_num
#                 # })
#             # else:
#             #     all_chunks.append({
#             #     "text": current_paragraph.strip(),
#             #     "page": page_num,
#             #     "type": "paragraph"
#             #     })
#                 # temp_doc = LlamaDocument(
#                 #     text=current_paragraph,
#                 #     metadata={"page": page_num}
#                 # )
#                 # nodes = splitter.get_nodes_from_documents([temp_doc])
#                 # chunk_list = [{
#                 #     "text": node.text,
#                 #     "page": page_num
#                 # } for node in nodes]
#                 # if len(chunk_list) > 1:
#                 #     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
#                 # all_chunks.extend(chunk_list)

#     return all_chunks
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
    for i, c in enumerate(chunks[:80 ]):  # يمكنك زيادة العدد أو استخدام len(chunks)
        print("="*40)
        print(f"CHUNK {i}")
        print(f"  page: {c.get('page')}")
        print(f"  section: {c.get('section')}")
        print(f"  type: {c.get('type', 'paragraph')}")
        print(f"  text length: {len(c['text'])}")
        print(f"  text preview: {c}...")
    print("="*60 + "\n")
    return chunks
