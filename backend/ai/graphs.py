from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from backend.ai.state import PaperState, TeamState
from backend.ai.agents import (
    classifier_node, chatbot_node, paper_qa_node,
    locate_paragraph_node, full_summary_node, external_concept_node, critic_node
)

# ------------------- Sub-graph for Paper Processing -------------------
def build_paper_graph(intent: str):
    workflow = StateGraph(PaperState)

    if intent == "paper_qa":
        workflow.add_node("paper_qa", paper_qa_node)
        workflow.add_node("critic", critic_node)
        workflow.set_entry_point("paper_qa")
        workflow.add_edge("paper_qa", "critic")
        workflow.add_conditional_edges(
            "critic",
            lambda s: END if s.get("final_answer") else "paper_qa",
            {"paper_qa": "paper_qa", END: END}
        )
    elif intent == "locate_paragraph":
        workflow.add_node("locate", locate_paragraph_node)
        workflow.add_node("critic", critic_node)
        workflow.set_entry_point("locate")
        workflow.add_edge("locate", "critic")
        workflow.add_conditional_edges(
            "critic",
            lambda s: END if s.get("final_answer") else "locate",
            {"locate": "locate", END: END}
        )
    elif intent == "full_summary":
        workflow.add_node("summary", full_summary_node)
        workflow.add_node("critic", critic_node)
        workflow.set_entry_point("summary")
        workflow.add_edge("summary", "critic")
        workflow.add_conditional_edges(
            "critic",
            lambda s: END if s.get("final_answer") else "summary",
            {"summary": "summary", END: END}
        )
    elif intent == "external_concept":
        workflow.add_node("web", external_concept_node)
        workflow.add_node("critic", critic_node)
        workflow.set_entry_point("web")
        workflow.add_edge("web", "critic")
        workflow.add_conditional_edges(
            "critic",
            lambda s: END if s.get("final_answer") else "web",
            {"web": "web", END: END}
        )
    else:
        # fallback
        workflow.add_node("paper_qa", paper_qa_node)
        workflow.add_node("critic", critic_node)
        workflow.set_entry_point("paper_qa")
        workflow.add_edge("paper_qa", "critic")
        workflow.add_conditional_edges(
            "critic",
            lambda s: END if s.get("final_answer") else "paper_qa",
            {"paper_qa": "paper_qa", END: END}
        )

    return workflow.compile(checkpointer=InMemorySaver())

# ------------------- Paper Team Node (Wrapper for Sub-graph) -------------------
def paper_team_node(state: TeamState):
    intent = state["next_step"]
    query = state["messages"][-1].content

    paper_input = {
        "query": query,
        "section_filter": state.get("section_filter"),
        "page_hint": state.get("page_hint"),
        "revision_number": 0
    }

    graph = build_paper_graph(intent)
    result = graph.invoke(paper_input)

    final = result.get("final_answer", "I couldn't generate an answer.")
    print(f"\n🚀 [Paper Team] تشغيل الرسم الفرعي للنية: {intent}")
    print(f"   السؤال: {query[:100]}...")
    return {"final_response": final}

# ------------------- Master Graph -------------------
def build_master_graph():
    workflow = StateGraph(TeamState)

    workflow.add_node("classifier", classifier_node)
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("paper_team", paper_team_node)

    workflow.set_entry_point("classifier")

    def router(state: TeamState):
        nxt = state["next_step"]
        if nxt in ["paper_qa", "locate_paragraph", "full_summary", "external_concept"]:
            return "paper_team"
        else:
            return "chatbot"

    workflow.add_conditional_edges(
        "classifier",
        router,
        {"paper_team": "paper_team", "chatbot": "chatbot"}
    )

    workflow.add_edge("chatbot", END)
    workflow.add_edge("paper_team", END)

    return workflow.compile(checkpointer=InMemorySaver())

master_graph = build_master_graph()