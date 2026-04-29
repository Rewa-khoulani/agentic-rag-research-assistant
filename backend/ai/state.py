from typing import Annotated, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict

class PaperState(TypedDict):
    """حالة الـ Sub-graph الخاص بمعالجة الأسئلة على ورقة واحدة"""
    query: str
    section_filter: Optional[str]
    page_hint: Optional[int]
    retrieved_context: str
    raw_data: Optional[str]
    draft_answer: str
    critique: Optional[str]
    final_answer: str
    revision_number: int
    needs_web: bool

class TeamState(TypedDict):
    """حالة الـ Master Graph"""
    messages: Annotated[List[BaseMessage], add_messages]
    next_step: str
    section_filter: Optional[str]
    page_hint: Optional[int]
    paper_loaded: bool
    final_response: Optional[str]
    forced_intent: Optional[str] #  للقسم أو الفقرة المحددةclassifier لتجاوز