import re
from typing import List, Dict, Any

# ========== دوال معالجة الجداول والنصوص (كودك الأصلي) ==========
def is_table_line(line: str) -> bool:
    return "|" in line and len(line.split("|")) > 2

def table_to_text(table_text: str) -> str:
    # تنظيف وسوم HTML الشائعة
    table_text = table_text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    lines = [l.strip() for l in table_text.split("\n") if l.strip()]
    if len(lines) < 2:
        return table_text

    header = [h.strip().replace("*", "") for h in lines[0].split("|") if h.strip()]
    output = []
    first_col_name = header[0] if header else "Entry"

    for row in lines[1:]:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        if len(cols) != len(header):
            continue
        identifier = cols[0].strip()
        if not identifier or identifier.replace('-', '').strip() == '':
            continue
        sentence = f"{first_col_name} {identifier} has:\n"
        for h, c in zip(header[1:], cols[1:]):
            if c.strip() not in ["", "-", "--", "---", "—"]:
                sentence += f"- {h}: {c}\n"
        output.append(sentence.strip())
    return "\n\n".join(output)
# def is_table_line(line: str) -> bool:
#     return "|" in line and len(line.split("|")) > 2

# def table_to_text(table_text: str) -> str:
#     lines = [l.strip() for l in table_text.split("\n") if l.strip()]
#     if len(lines) < 2:
#         return table_text
#     header = [h.strip().replace("*", "") for h in lines[0].split("|") if h.strip()]
#     output = []
#     for row in lines[1:]:
#         cols = [c.strip() for c in row.split("|") if c.strip()]
#         if len(cols) != len(header):
#             continue
#         model_name = cols[header.index("Model")] if "Model" in header else cols[0]
#         sentence = f"Model {model_name} has:\n"
#         for h, c in zip(header, cols):
#             if h.lower() != "model" and c not in ["-", ""]:
#                 sentence += f"- {h}: {c}\n"
#         output.append(sentence.strip())
#     return "\n\n".join(output)
# def table_to_text(table_text: str) -> str:
#     # تنظيف وسوم HTML الشائعة
#     table_text = table_text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
#     lines = [l.strip() for l in table_text.split("\n") if l.strip()]
#     if len(lines) < 2:
#         return table_text

#     header = [h.strip().replace("*", "") for h in lines[0].split("|") if h.strip()]
#     output = []

#     # تحديد اسم العمود الأول لاستخدامه في الجملة (بدلاً من كلمة "Model" الثابتة)
#     first_col_name = header[0] if header else "Entry"

#     for row in lines[1:]:
#         cols = [c.strip() for c in row.split("|") if c.strip()]
#         if len(cols) != len(header):
#             continue

#         # المعرف (أول قيمة) – قد يكون اسم القاعدة أو شرطات فاصلة
#         identifier = cols[0].strip()

#         # تجاهل الصف إذا كان المعرف فارغًا أو مجرد شرطات (--- / -- / -)
#         if not identifier or identifier.replace('-', '').strip() == '':
#             continue

#         # بناء الجملة الوصفية
#         sentence = f"{first_col_name} {identifier} has:\n"
#         for h, c in zip(header[1:], cols[1:]):   # نبدأ من ثاني عمود لتفادي تكرار المعرف
#             if c.strip() not in ["", "-", "--", "---", "—"]:
#                 sentence += f"- {h}: {c}\n"
#         output.append(sentence.strip())

#     return "\n\n".join(output)

# def table_to_text(table_text: str) -> str:
    # إزالة وسوم HTML الشائعة
    table_text = table_text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    lines = [l.strip() for l in table_text.split("\n") if l.strip()]
    if len(lines) < 2:
        return table_text

    header = [h.strip().replace("*", "") for h in lines[0].split("|") if h.strip()]
    output = []

    # اسم العمود الأول (لنفترض أنه Dataset، أو أي شيء آخر)
    first_col_name = header[0] if header else "Entry"

    for row in lines[1:]:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        if len(cols) != len(header):
            continue

        identifier = cols[0].strip()

        # تجاهل الصف إذا كان المعرف فارغاً أو مجرد شرطات
        if not identifier or identifier.replace('-', '').strip() == '':
            continue

        # بناء الجملة الوصفية
        sentence = f"{first_col_name} {identifier} has:\n"
        for h, c in zip(header[1:], cols[1:]):
            if c.strip() not in ["", "-", "--", "---", "—"]:
                sentence += f"- {h}: {c}\n"
        output.append(sentence.strip())

    return "\n\n".join(output)
# def table_to_text(table_text: str) -> str:
#     # تنظيف أولي
#     table_text = table_text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
#     lines = [l.strip() for l in table_text.split("\n") if l.strip()]
#     if len(lines) < 2:
#         return table_text

#     # تجاهل الأسطر الفارغة وأسطر الفواصل (مثل |---|---|)
#     data_lines = []
#     for l in lines:
#         if re.match(r'^\|[\s\-:|]+\|$', l):  # سطر فاصل أو شبه فارغ
#             continue
#         if l.count('|') >= 2:
#             data_lines.append(l)

#     if not data_lines:
#         return table_text

#     # استخراج الهيدر من أول سطر يحتوي على خلايا غير فارغة
#     header = None
#     header_idx = -1
#     for i, l in enumerate(data_lines):
#         parts = [c.strip() for c in l.split("|") if c.strip()]
#         if parts and not all(p in ['', '-', '--', '---', '—'] for p in parts):
#             header = parts
#             header_idx = i
#             break

#     if header is None:
#         return table_text

#     output = []
#     first_col_name = header[0].strip("*") if header else "Entry"

#     for l in data_lines[header_idx+1:]:
#         cols = [c.strip() for c in l.split("|") if c.strip()]
#         if not cols:
#             continue
#         # إذا كان عدد الأعمدة أقل، نمددها بقيم فارغة
#         while len(cols) < len(header):
#             cols.append("")
#         identifier = cols[0].strip()
#         if not identifier or identifier.replace('-', '').strip() == '':
#             continue

#         sentence = f"{first_col_name} {identifier} has:\n"
#         for h, c in zip(header[1:], cols[1:]):
#             if h and c and c.strip() not in ["", "-", "--", "---", "—"]:
#                 sentence += f"- {h}: {c}\n"
#         output.append(sentence.strip())

#     return "\n\n".join(output) if output else table_text
# def table_to_text(table_text: str) -> str:
#     """
#     Converts a markdown table string into a human-readable text format.
#     It skips empty rows and separator rows (e.g., |---|---|).
#     If a column named 'Model' exists, it is used as the entry name.
#     Otherwise, the first column is used with the label 'Entry'.
#     """
#     # 1. Clean up HTML break tags
#     text = table_text.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')

#     # 2. Split and filter lines
#     lines = [l.strip() for l in text.split("\n") if l.strip()]
#     if len(lines) < 2:
#         return text

#     # Filter out separator lines like |---|:---|
#     data_lines = []
#     for l in lines:
#         # If it's just dashes, pipes, colons, spaces -> skip
#         if re.match(r'^\|[\s\-:|]+\|$', l):
#             continue
#         data_lines.append(l)

#     if not data_lines:
#         return text

#     # 3. Find header (first line with actual content)
#     header = None
#     header_idx = -1
#     for i, l in enumerate(data_lines):
#         parts = [c.strip() for c in l.split("|") if c.strip()]
#         if parts and not all(p in ['', '-', '--', '---', '—'] for p in parts):
#             header = [h.strip('*').strip() for h in parts]
#             header_idx = i
#             break

#     if header is None:
#         return text

#     # 4. Determine the key column
#     model_key_idx = None
#     # Try to find a column named 'Model'
#     for idx, h in enumerate(header):
#         if h.lower() == 'model':
#             model_key_idx = idx
#             break

#     if model_key_idx is not None:
#         first_col_name = "Model"
#     else:
#         # Use the first column
#         model_key_idx = 0
#         first_col_name = header[0] if header else "Entry"
#         # Avoid ugly names like 'Ref' if possible, but if that's the header, we keep it.
#         # If the header is empty, default to 'Entry'
#         if not first_col_name:
#             first_col_name = "Entry"

#     output = []

#     # 5. Process data rows
#     for l in data_lines[header_idx+1:]:
#         cols = [c.strip() for c in l.split("|") if c.strip()]
#         if not cols:
#             continue

#         # Ensure cols has at least as many items as header
#         while len(cols) < len(header):
#             cols.append("")

#         identifier = cols[model_key_idx].strip()
#         # Skip rows where the identifier is empty or just dashes
#         if not identifier or identifier.replace('-', '').strip() == '':
#             continue

#         # Build sentence
#         sentence = f"{first_col_name} {identifier} has:\n"
#         for h, c in zip(header, cols):
#             # Skip the key column itself
#             if h == header[model_key_idx]:
#                 continue
#             # Skip empty or dash values
#             if not c or c.strip() in ["-", "--", "---", "—"]:
#                 continue
#             sentence += f"- {h}: {c}\n"

#         output.append(sentence.strip())

#     return "\n\n".join(output) if output else text
#  ========== دوال بيانات الأقسام والتراكب (كودك الأصلي) ==========

def add_section_metadata(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    current_section = "General"
    for chunk in chunks:
        text = chunk["text"].strip()
        if text.startswith('#'):
            first_line = text.split('\n')[0]
            section = re.sub(r'^#+\s*', '', first_line).strip()
            section = re.sub(r'\*\*|__', '', section)  # إزالة bold
            section = re.sub(r'\*|_', '', section) 
            # current_section = re.sub(r'^#+\s*', '', first_line).strip()
            current_section = section.strip()
        chunk["section"] = current_section
    return chunks

def apply_overlap_to_chunks(chunks: List[Dict[str, Any]], overlap_size: int = 50) -> List[Dict[str, Any]]:
    """
    يأخذ آخر جمل/سطور من chunk السابق ويضيفها للبداية التالية
    """
    if len(chunks) <= 1:
        return chunks
    new_chunks = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_text = new_chunks[-1]["text"].split("\n")
        # نأخذ آخر 2 أسطر (خفيف وآمن)
        overlap_text = "\n".join(prev_text[-overlap_size:])
        chunks[i]["text"] = overlap_text + "\n" + chunks[i]["text"]
        new_chunks.append(chunks[i])
    return new_chunks

# ========== دوال مساعدة جديدة لـ Agent (لا تؤثر على المعالجة) ==========

SECTION_KEYWORDS = {
    "مقدمة": ["مقدمة", "المقدمة", "introduction", "intro"],
    "منهجية": ["منهجية", "المنهجية", "methodology", "methods", "طريقة", "الطريقة"],
    "نتائج": ["نتائج", "النتائج", "results", "findings"],
    "مناقشة": ["مناقشة", "المناقشة", "discussion"],
    "خاتمة": ["خاتمة", "الخاتمة", "conclusion", "استنتاج", "الاستنتاج"],
    "مراجع": ["مراجع", "المراجع", "references"],
}

def extract_section_from_query(query: str, available_sections: List[str]) -> str | None:
    """استخراج القسم المذكور في السؤال إن وجد (تستخدم في الـ Agent)"""
    query_lower = query.lower()
    for section in available_sections:
        if section.lower() in query_lower:
            return section
    for arabic_section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                for avail in available_sections:
                    if arabic_section.lower() in avail.lower():
                        return avail
    return None

def get_available_sections(collection) -> List[str]:
    """استرجاع جميع الأقسام الفريدة من قاعدة البيانات (تستخدم في الـ Agent)"""
    all_metadatas = collection.get()["metadatas"]
    sections = set()
    for meta in all_metadatas:
        sec = meta.get("section", "General")
        if sec and sec != "N/A":
            sections.add(sec)
    return sorted(list(sections))


def get_available_pages(collection) -> List[int]:
    """استرجاع جميع أرقام الصفحات الفريدة من قاعدة البيانات"""
    all_metadatas = collection.get()["metadatas"]
    pages = set()
    for meta in all_metadatas:
        page = meta.get("page", "N/A")
        if page and page != "N/A":
            try:
                pages.add(int(page))
            except ValueError:
                pass
    return sorted(list(pages))