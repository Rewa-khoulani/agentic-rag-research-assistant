import pymupdf4llm
import fitz
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument
import re
import pdfplumber

from config import CHUNK_SIZE, CHUNK_OVERLAP
from backend.utils import (
    is_table_line,
    table_to_text,
    add_section_metadata,
    apply_overlap_to_chunks
)





# from langchain_opendataloader_pdf import OpenDataLoaderPDFLoader
# from langchain_core.documents import Document
# from typing import List

# def load_pdf_as_documents(pdf_file: str) -> List[Document]:
#     """
#     تستخدم OpenDataLoader PDF لاستخراج النص من ملف PDF بصيغة Markdown.
#     هذا يعطي نتائج أفضل بكثير للجداول والعناوين وهيكل المستند.
#     """
#     print(f"📄 جاري استخراج النص باستخدام OpenDataLoader PDF...")
    
#     try:
#         # استخدام markdown format للحصول على أفضل جودة للعناوين والجداول
#         loader = OpenDataLoaderPDFLoader(
#             file_path=pdf_file,
#             format="markdown",        # Markdown يحافظ على العناوين والجداول
#             split_pages=True,         # يقسم المستند إلى صفحات منفصلة
#             reading_order="xycut",    # خوارزمية XY-Cut++ للقراءة الصحيحة متعددة الأعمدة
#             table_method="default",   # تعرف على الجداول بناءً على الحدود
#             quiet=False               # إظهار سجل التقدم
#         )
        
#         documents = loader.load()
#         print(f"✅ تم استخراج {len(documents)} صفحة باستخدام OpenDataLoader PDF")
        
#         # تأكد من أن كل وثيقة تحمل metadata صحيح لرقم الصفحة
#         for i, doc in enumerate(documents):
#             if 'page' not in doc.metadata:
#                 doc.metadata['page'] = i + 1
        
#         return documents
        
#     except Exception as e:
#         print(f"⚠️ فشل OpenDataLoader PDF: {e}")
#         print("🔄 العودة إلى PyMuPDF4LLM كخيار احتياطي...")
#         return _load_with_pymupdf4llm(pdf_file)


# def _load_with_pymupdf4llm(pdf_file: str) -> List[Document]:
#     """خيار احتياطي: استخراج النص باستخدام PyMuPDF4LLM."""
#     import pymupdf4llm
#     import fitz
    
#     pdf_document = fitz.open(pdf_file)
#     documents = []
#     for page_num in range(len(pdf_document)):
#         try:
#             page_md = pymupdf4llm.to_markdown(pdf_file, pages=[page_num])
#         except TypeError:
#             page = pdf_document[page_num]
#             page_md = page.get_text()
#         documents.append(Document(
#             text=page_md,
#             metadata={"page": page_num + 1}
#         ))
#     return documents

# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
#     print("Documents received:", len(documents))
#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     all_chunks = []

#     for doc in documents:
#         # ---------- توافق مع LangChain Document و llama_index Document ----------
#         text = getattr(doc, 'page_content', None) or getattr(doc, 'text', '')
#         page_num = doc.metadata.get("page") or doc.metadata.get("page_label", 0)

#         # ---------- طباعة النص المستخرج من الصفحة ----------
#         print(f"\n📄 الصفحة {page_num} – إجمالي الأحرف: {len(text)}")
#         print("-" * 50)
#         print(text[:3000])  # أول 300 حرف كمعاينة
#         if len(text) > 300:
#             print("...")
#         print("-" * 50)

#         lines = text.split('\n')
#         current_paragraph = ""
#         inside_table = False
#         table_buffer = ""
#         post_table = False

#         for line in lines:
#             # --- التعرف على بداية جدول ---
#             is_table = is_table_line(line) or line.strip().startswith('|') or '<table>' in line.lower()
#             if is_table:
#                 inside_table = True
#                 table_buffer += line + "\n"
#                 post_table = False
#                 continue

#             # --- الخروج من الجدول ---
#             elif inside_table:
#                 table_text = table_buffer.strip()
#                 structured_table = table_to_text(table_text)
#                 if not structured_table.strip():
#                     structured_table = table_text
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page_num,
#                     "type": "table"
#                 })
#                 table_buffer = ""
#                 inside_table = False
#                 post_table = True

#             # --- انتظار تسمية بعد الجدول ---
#             if post_table:
#                 if not line.strip():
#                     continue
#                 if re.match(r'(Table|Figure|جدول|شكل)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
#                     caption = line.strip()
#                     if all_chunks and all_chunks[-1]["type"] == "table":
#                         all_chunks[-1]["text"] += "\n" + caption
#                     post_table = False
#                     continue
#                 else:
#                     post_table = False

#             # --- عنوان ---
#             is_heading = re.match(r'^\s*#{1,6}\s+', line)
#             if is_heading:
#                 if current_paragraph.strip():
#                     estimated_tokens = len(current_paragraph.split()) * 1.3
#                     if estimated_tokens <= chunk_size:
#                         all_chunks.append({"text": current_paragraph.strip(), "page": page_num})
#                     else:
#                         _split_and_add(current_paragraph, page_num, splitter, chunk_size, all_chunks)
#                 current_paragraph = line
#                 continue

#             # --- سطر عادي (يُضاف للفقرة الحالية) ---
#             if current_paragraph:
#                 current_paragraph += "\n" + line
#             else:
#                 current_paragraph = line

#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens > chunk_size * 1.2:
#                 _split_and_add(current_paragraph, page_num, splitter, chunk_size, all_chunks)
#                 current_paragraph = ""

#         # --- نهاية الصفحة: أي جدول متبقٍ ---
#         if inside_table and table_buffer.strip():
#             structured_table = table_to_text(table_buffer)
#             all_chunks.append({
#                 "text": structured_table,
#                 "page": page_num,
#                 "type": "table"
#             })

#         # --- الفقرة المتبقية ---
#         if current_paragraph.strip():
#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens <= chunk_size * 1.2:
#                 all_chunks.append({"text": current_paragraph.strip(), "page": page_num})
#             else:
#                 _split_and_add(current_paragraph, page_num, splitter, chunk_size, all_chunks)

#     return all_chunks
# # تبع لانغ تشين 

# # دالة مساعدة لاستخراج القطع من الفقرات الطويلة

# def _split_and_add(text, page_num, splitter, chunk_size, all_chunks):
#     temp_doc = LlamaDocument(text=text, metadata={"page": page_num})
#     nodes = splitter.get_nodes_from_documents([temp_doc])
#     chunk_list = [{"text": node.text, "page": page_num} for node in nodes]
#     if len(chunk_list) > 1:
#         chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=20)
#     all_chunks.extend(chunk_list)


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

# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
#     print("Documents received:", len(documents))
#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     all_chunks = []

#     for doc in documents:
#         page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
#         text = doc.text
#         lines = text.split('\n')
#         current_paragraph = ""
#         inside_table = False
#         table_buffer = ""

#         for line in lines:
#             if is_table_line(line):
#                 inside_table = True
#                 table_buffer += line + "\n"
#                 continue
#             elif inside_table:
#                 table_text = table_buffer.strip()
#                 structured_table = table_to_text(table_text)
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page_num,
#                     "type": "table"
#                 })
#                 table_buffer = ""
#                 inside_table = False

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
#                             chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
#                         all_chunks.extend(chunk_list)
#                 current_paragraph = line
#                 continue

#             if current_paragraph:
#                 current_paragraph += "\n" + line
#             else:
#                 current_paragraph = line

#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens > chunk_size * 1.5:
#                 temp_doc = LlamaDocument(
#                     text=current_paragraph,
#                     metadata={"page": page_num}
#                 )
#                 nodes = splitter.get_nodes_from_documents([temp_doc])
#                 chunk_list = [{
#                     "text": node.text,
#                     "page": page_num
#                 } for node in nodes]
#                 if len(chunk_list) > 1:
#                     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
#                 all_chunks.extend(chunk_list)
#                 current_paragraph = ""

#         # if inside_table and table_buffer.strip():
#         #     structured_table = table_to_text(table_buffer)
#         #     all_chunks.append({
#         #         "text": structured_table,
#         #         "page": page_num,
#         #         "type": "table"
#         #     })
#             elif inside_table:
#                 # انتهى الجدول
#                 table_text = table_buffer.strip()
#                 structured_table = table_to_text(table_text)

#                 # ---------- التقاط التسمية التوضيحية (Caption) ----------
#                 caption = None
#                 # نمط يطابق "Table 1:", "الجدول 2:", "Table III." إلخ
#                 if re.match(r'^(Table|جدول)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
#                     caption = line.strip()
#                     # ضم التسمية إلى نص الجدول
#                     structured_table += "\n" + caption

#                 # إضافة الجدول كقطعة مستقلة
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page_num,
#                     "type": "table"
#                 })

#                 # إعادة تعيين المتغيرات
#                 table_buffer = ""
#                 inside_table = False

#                 # إذا التقطنا تسمية، نتجاوز هذا السطر (لا يُضاف للفقرة الحالية)
#                 if caption:
#                     continue
#                 # وإلا، سيكمل الكود طبيعياً ليعالج السطر الحالي أسفله
#         if current_paragraph.strip():
#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens <= chunk_size:
#                 all_chunks.append({
#                     "text": current_paragraph.strip(),
#                     "page": page_num
#                 })
#             else:
#                 temp_doc = LlamaDocument(
#                     text=current_paragraph,
#                     metadata={"page": page_num}
#                 )
#                 nodes = splitter.get_nodes_from_documents([temp_doc])
#                 chunk_list = [{
#                     "text": node.text,
#                     "page": page_num
#                 } for node in nodes]
#                 if len(chunk_list) > 1:
#                     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
#                 all_chunks.extend(chunk_list)
#     return all_chunks
# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    # print("Documents received:", len(documents))
    # splitter = SentenceSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap
    # )
    # all_chunks = []

    # for doc in documents:
    #     page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
    #     text = doc.text
    #     lines = text.split('\n')
    #     current_paragraph = ""
    #     inside_table = False
    #     table_buffer = ""

    #     for line in lines:
    #         if is_table_line(line):
    #             inside_table = True
    #             table_buffer += line + "\n"
    #             continue
    #         elif inside_table:
    #             # انتهى الجدول
    #             table_text = table_buffer.strip()
    #             structured_table = table_to_text(table_text)

    #             # ---------- التقاط التسمية التوضيحية (Caption) ----------
    #             caption = None
    #             # نمط يطابق "Table 1:", "الجدول 2:", "Table III." إلخ
    #             if re.match(r'^(Table|جدول)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
    #                 caption = line.strip()
    #                 # ضم التسمية إلى نص الجدول
    #                 structured_table += "\n" + caption

    #             # إضافة الجدول كقطعة مستقلة
    #             all_chunks.append({
    #                 "text": structured_table,
    #                 "page": page_num,
    #                 "type": "table"
    #             })

    #             # إعادة تعيين المتغيرات
    #             table_buffer = ""
    #             inside_table = False

    #             # إذا التقطنا تسمية، نتجاوز هذا السطر (لا يُضاف للفقرة الحالية)
    #             if caption:
    #                 continue
    #             # وإلا، سيكمل الكود طبيعياً ليعالج السطر الحالي أسفله

    #         is_heading = re.match(r'^\s*#{1,6}\s+', line)
    #         if is_heading:
    #             if current_paragraph.strip():
    #                 estimated_tokens = len(current_paragraph.split()) * 1.3
    #                 if estimated_tokens <= chunk_size:
    #                     all_chunks.append({
    #                         "text": current_paragraph.strip(),
    #                         "page": page_num
    #                     })
    #                 else:
    #                     temp_doc = LlamaDocument(
    #                         text=current_paragraph,
    #                         metadata={"page": page_num}
    #                     )
    #                     nodes = splitter.get_nodes_from_documents([temp_doc])
    #                     chunk_list = [{
    #                         "text": node.text,
    #                         "page": page_num
    #                     } for node in nodes]
    #                     if len(chunk_list) > 1:
    #                         chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #                     all_chunks.extend(chunk_list)
    #             current_paragraph = line
    #             continue

    #         if current_paragraph:
    #             current_paragraph += "\n" + line
    #         else:
    #             current_paragraph = line

    #         estimated_tokens = len(current_paragraph.split()) * 1.3
    #         if estimated_tokens > chunk_size * 1.5:
    #             temp_doc = LlamaDocument(
    #                 text=current_paragraph,
    #                 metadata={"page": page_num}
    #             )
    #             nodes = splitter.get_nodes_from_documents([temp_doc])
    #             chunk_list = [{
    #                 "text": node.text,
    #                 "page": page_num
    #             } for node in nodes]
    #             if len(chunk_list) > 1:
    #                 chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #             all_chunks.extend(chunk_list)
    #             current_paragraph = ""

    #     # معالجة نهاية الصفحة (كما هي سابقاً)
    #     if current_paragraph.strip():
    #         estimated_tokens = len(current_paragraph.split()) * 1.3
    #         if estimated_tokens <= chunk_size:
    #             all_chunks.append({
    #                 "text": current_paragraph.strip(),
    #                 "page": page_num
    #             })
    #         else:
    #             temp_doc = LlamaDocument(
    #                 text=current_paragraph,
    #                 metadata={"page": page_num}
    #             )
    #             nodes = splitter.get_nodes_from_documents([temp_doc])
    #             chunk_list = [{
    #                 "text": node.text,
    #                 "page": page_num
    #             } for node in nodes]
    #             if len(chunk_list) > 1:
    #                 chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #             all_chunks.extend(chunk_list)

    # return all_chunks
# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    # print("Documents received:", len(documents))
    # splitter = SentenceSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap
    # )
    # all_chunks = []

    # for doc in documents:
    #     page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
    #     text = doc.text
    #     lines = text.split('\n')
    #     current_paragraph = ""
    #     inside_table = False
    #     table_buffer = ""

    #     for line in lines:
    #         # ------ حالة جدول ------
    #         if is_table_line(line):
    #             inside_table = True
    #             table_buffer += line + "\n"
    #             continue

    #         elif inside_table:
    #             # انتهى الجدول
    #             table_text = table_buffer.strip()
    #             structured_table = table_to_text(table_text)
    #             # أضف النص المنظّم للجدول إلى الفقرة الحالية (وليس كقطعة منفصلة)
    #             if current_paragraph:
    #                 current_paragraph += "\n\n" + structured_table
    #             else:
    #                 current_paragraph = structured_table
    #             table_buffer = ""
    #             inside_table = False
    #             # تابع معالجة السطر الحالي (الذي ليس جزءاً من الجدول) كجزء من الفقرة
    #             # لا تستخدم continue هنا، بل دع الكود يكمل بشكل طبيعي ليضيف السطر إلى current_paragraph

    #         # ------ حالة عنوان ------
    #         is_heading = re.match(r'^\s*#{1,6}\s+', line)
    #         if is_heading:
    #             if current_paragraph.strip():
    #                 estimated_tokens = len(current_paragraph.split()) * 1.3
    #                 if estimated_tokens <= chunk_size:
    #                     all_chunks.append({
    #                         "text": current_paragraph.strip(),
    #                         "page": page_num
    #                     })
    #                 else:
    #                     temp_doc = LlamaDocument(
    #                         text=current_paragraph,
    #                         metadata={"page": page_num}
    #                     )
    #                     nodes = splitter.get_nodes_from_documents([temp_doc])
    #                     chunk_list = [{
    #                         "text": node.text,
    #                         "page": page_num
    #                     } for node in nodes]
    #                     if len(chunk_list) > 1:
    #                         chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #                     all_chunks.extend(chunk_list)
    #             # ابدأ فقرة جديدة بالعنوان
    #             current_paragraph = line
    #             continue

    #         # ------ سطر عادي ------
    #         if current_paragraph:
    #             current_paragraph += "\n" + line
    #         else:
    #             current_paragraph = line

    #         estimated_tokens = len(current_paragraph.split()) * 1.3
    #         if estimated_tokens > chunk_size * 1.5:
    #             temp_doc = LlamaDocument(
    #                 text=current_paragraph,
    #                 metadata={"page": page_num}
    #             )
    #             nodes = splitter.get_nodes_from_documents([temp_doc])
    #             chunk_list = [{
    #                 "text": node.text,
    #                 "page": page_num
    #             } for node in nodes]
    #             if len(chunk_list) > 1:
    #                 chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #             all_chunks.extend(chunk_list)
    #             current_paragraph = ""

    #     # بعد انتهاء الصفحة
    #     if inside_table and table_buffer.strip():
    #         structured_table = table_to_text(table_buffer)
    #         # أضف الجدول المتبقي للفقرة الحالية
    #         if current_paragraph:
    #             current_paragraph += "\n\n" + structured_table
    #         else:
    #             current_paragraph = structured_table

    #     if current_paragraph.strip():
    #         estimated_tokens = len(current_paragraph.split()) * 1.3
    #         if estimated_tokens <= chunk_size:
    #             all_chunks.append({
    #                 "text": current_paragraph.strip(),
    #                 "page": page_num
    #             })
    #         else:
    #             temp_doc = LlamaDocument(
    #                 text=current_paragraph,
    #                 metadata={"page": page_num}
    #             )
    #             nodes = splitter.get_nodes_from_documents([temp_doc])
    #             chunk_list = [{
    #                 "text": node.text,
    #                 "page": page_num
    #             } for node in nodes]
    #             if len(chunk_list) > 1:
    #                 chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
    #             all_chunks.extend(chunk_list)

    # return all_chunks
# def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
#     print("Documents received:", len(documents))
#     splitter = SentenceSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=chunk_overlap
#     )
#     all_chunks = []

#     for doc in documents:
#         page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
#         text = doc.text
#         lines = text.split('\n')
#         current_paragraph = ""
#         inside_table = False
#         table_buffer = ""

#         for line in lines:
#             if is_table_line(line):
#                 inside_table = True
#                 table_buffer += line + "\n"
#                 continue

#             elif inside_table:
#                 # انتهى الجدول
#                 table_text = table_buffer.strip()
#                 structured_table = table_to_text(table_text)

#                 # ---------- التقاط التسمية التوضيحية (Caption) ----------
#                 caption = None
#                 # نمط يطابق "Table 1:", "الجدول 2:", "Table III." إلخ
#                 if re.match(r'^(Table|table)\s*[\dIVX]+[:.]', line, re.IGNORECASE):
#                     caption = line.strip()
#                     # ضم التسمية إلى نص الجدول
#                     structured_table += "\n" + caption

#                 # إضافة الجدول كقطعة مستقلة
#                 all_chunks.append({
#                     "text": structured_table,
#                     "page": page_num,
#                     "type": "table"
#                 })

#                 # إعادة تعيين المتغيرات
#                 table_buffer = ""
#                 inside_table = False

#                 # إذا التقطنا تسمية، نتجاوز هذا السطر (لا يُضاف للفقرة الحالية)
#                 if caption:
#                     continue
#                 # وإلا، سيكمل الكود طبيعياً ليعالج السطر الحالي أسفله

#             # ------ حالة عنوان ------
#             is_heading = re.match(r'^\s*#{1,6}\s+', line)
#             if is_heading:
#                 if current_paragraph.strip():
#                     # ... (معالجة الفقرة الحالية مثل السابق)
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
#                             chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
#                         all_chunks.extend(chunk_list)
#                 current_paragraph = line
#                 continue

#             # ------ سطر عادي ------
#             if current_paragraph:
#                 current_paragraph += "\n" + line
#             else:
#                 current_paragraph = line

#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens > chunk_size * 1.5:
#                 temp_doc = LlamaDocument(
#                     text=current_paragraph,
#                     metadata={"page": page_num}
#                 )
#                 nodes = splitter.get_nodes_from_documents([temp_doc])
#                 chunk_list = [{
#                     "text": node.text,
#                     "page": page_num
#                 } for node in nodes]
#                 if len(chunk_list) > 1:
#                     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=2)
#                 all_chunks.extend(chunk_list)
#                 current_paragraph = ""

#         # معالجة ما تبقى في نهاية الصفحة (جدول أخير + فقرة)
#         if inside_table and table_buffer.strip():
#             structured_table = table_to_text(table_buffer)
#             all_chunks.append({
#                 "text": structured_table,
#                 "page": page_num,
#                 "type": "table"
#             })

#         if current_paragraph.strip():
#             estimated_tokens = len(current_paragraph.split()) * 1.3
#             if estimated_tokens <= chunk_size:
#                 all_chunks.append({
#                     "text": current_paragraph.strip(),
#                     "page": page_num
#                 })
#             else:
#                 temp_doc = LlamaDocument(
#                     text=current_paragraph,
#                     metadata={"page": page_num}
#                 )
#                 nodes = splitter.get_nodes_from_documents([temp_doc])
#                 chunk_list = [{
#                     "text": node.text,
#                     "page": page_num
#                 } for node in nodes]
#                 if len(chunk_list) > 1:
#                     chunk_list = apply_overlap_to_chunks(chunk_list, overlap_size=50)
#                 all_chunks.extend(chunk_list)

#     return all_chunks
def smart_chunking(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    print("Documents received:", len(documents))
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    all_chunks = []

    for doc in documents:
        page_num = doc.metadata.get("page", doc.metadata.get("page_label"))
        text = doc.text
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
