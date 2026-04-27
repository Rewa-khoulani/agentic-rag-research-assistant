# from langchain_core.prompts import ChatPromptTemplate

# classifier_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an intent classifier for a research paper assistant.
# Analyze the user's question and determine the intent from these options:
# - 'locate_paragraph': User asks to explain a specific paragraph (mentions page number or quotes text).
# - 'full_summary': User asks for a complete summary/explanation of the whole paper.
# - 'paper_qa': User asks a general question that can be answered from the paper's content.
# - 'external_concept': User asks about a term/concept not explained in the paper, requiring web search.
# - 'chat': Casual conversation or out-of-scope question.

# Also extract:
# - section: The section mentioned (e.g., 'Methodology', 'Results').
# - page_hint: Page number if explicitly mentioned.

# Return as JSON with intent, section (or null), page_hint (or null)."""),
#     ("user", "{input}")
# ])

# paper_qa_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert research assistant. Answer the question using ONLY the provided context from the paper.
# If the answer cannot be found, say 'Not found in the paper.' Cite page numbers when possible."""),
#     ("user", "Context:\n{context}\n\nQuestion: {query}")
# ])

# locate_paragraph_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert at explaining academic text. The user has asked about a specific paragraph from the paper.
# Provide a clear, detailed explanation of that paragraph in simple terms. Include the key points and their significance."""),
#     ("user", "Paragraph text:\n{context}\n\nUser question: {query}")
# ])

# full_summary_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert at summarizing research papers. The user wants a comprehensive summary.
# Use the provided context (which covers the entire paper broken into sections) to produce a structured summary.
# Include: Introduction, Methodology, Key Findings, Discussion, and Conclusion. Cite section names."""),
#     ("user", "Paper content by section:\n{context}\n\nSummarize the paper in detail.")
# ])

# web_merge_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert research assistant. The user asked about a concept that is not fully explained in the paper.
# You have information from the web. Combine the web information with the paper's context to give a comprehensive answer.
# Mention that the explanation comes from external sources."""),
#     ("user", "Paper context: {paper_context}\n\nWeb information: {web_data}\n\nQuestion: {query}")
# ])

# critic_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are a strict reviewer. Check if the draft answer accurately addresses the user's question using ONLY the provided sources.
# If the answer is accurate and complete, approve it. Otherwise, provide specific critique on what is missing or incorrect."""),
#     ("user", "Question: {query}\nDraft Answer: {draft}\nSources: {sources_summary}")
# ])
from langchain_core.prompts import ChatPromptTemplate

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an intent classifier for a research paper assistant.
Analyze the user's question and determine the intent from these options:
- 'locate_paragraph': User asks to explain a specific paragraph (mentions page number or quotes text).
- 'full_summary': User asks for a complete summary/explanation of the whole paper.
- 'paper_qa': User asks a general question that can be answered from the paper's content.
- 'external_concept': User asks about a term/concept not explained in the paper, requiring web search.
- 'chat': Casual conversation or out-of-scope question.

Also extract:
- section: The section mentioned (e.g., 'Methodology', 'Results').
- page_hint: Page number if explicitly mentioned.

Return as JSON with intent, section (or null), page_hint (or null)."""),
    ("user", "{input}")
])

paper_qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research assistant. Answer the question using ONLY the provided context from the paper.
If the answer cannot be found, say 'Not found in the paper.' Cite page numbers when possible."""),
    ("user", "Context:\n{context}\n\nQuestion: {query}")
])

# locate_paragraph_prompt = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert at explaining academic text. The user has asked about a specific paragraph from the paper.
# Provide a clear, detailed explanation of that paragraph in simple terms. Include the key points and their significance."""),
#     ("user", "Paragraph text:\n{context}\n\nUser question: {query}")
# ])
locate_paragraph_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research assistant. You will receive a paragraph from a paper and a user question.
Your task is to answer the user's question using ONLY that paragraph. You must adapt the structure and style of your answer to the user's specific request:

- **If the user asks for an explanation**: Provide a detailed breakdown. Use bullet points (•) for each key point. Explain the meaning of complex phrases, the implications of the findings, and how the ideas connect. Do not just rephrase.

- **If the user asks for a summary**: Write one or two concise paragraphs that capture the absolute core message. Preserve all named entities (model names, datasets, metrics). Remove only redundant examples.

- **If the user asks a specific factual question** (e.g., "What score did X achieve?", "Which technique was used?"): Answer in a single clear sentence. Directly quote the relevant part of the paragraph as evidence.

Whichever style you use, never add information from outside the provided paragraph."""),
    ("user", "Paragraph:\n{context}\n\nUser Question: {query}")
])

full_summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at summarizing research papers. The user wants a comprehensive summary.
Use the provided context (which covers the entire paper broken into sections) to produce a structured summary.
Include: Introduction, Methodology, Key Findings, Discussion, and Conclusion. Cite section names."""),
    ("user", "Paper content by section:\n{context}\n\nSummarize the paper in detail.")
])

web_merge_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research assistant. The user asked about a concept that is not fully explained in the paper.
You have information from the web. Combine the web information with the paper's context to give a comprehensive answer.
Mention that the explanation comes from external sources."""),
    ("user", "Paper context: {paper_context}\n\nWeb information: {web_data}\n\nQuestion: {query}")
])

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a strict reviewer. Check if the draft answer accurately addresses the user's question using ONLY the provided sources.
If the answer is accurate and complete, approve it. Otherwise, provide specific critique on what is missing or incorrect."""),
    ("user", "Question: {query}\nDraft Answer: {draft}\nSources: {sources_summary}")
])