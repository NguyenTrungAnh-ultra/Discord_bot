from langgraph.graph import StateGraph, END
from src.modules.deep_research.state import ResearchState
from src.modules.deep_research.nodes.translator import translate_query
from src.modules.deep_research.nodes.searcher import search_node
from src.modules.deep_research.nodes.dispatcher import dispatch_node
from src.modules.deep_research.nodes.processor import process_node
from src.modules.deep_research.nodes.storer import store_node
from src.modules.deep_research.nodes.reporter import report_node

def should_continue(state: ResearchState):
    """Determines whether to continue processing URLs or generate the report."""
    if state.get("current_url") and state.get("iteration", 0) < state.get("max_iterations", 5):
        return "processor"
    return "reporter"

def create_research_graph():
    """Creates and compiles the LangGraph for deep research."""
    workflow = StateGraph(ResearchState)
    
    # Add Nodes
    workflow.add_node("translator", translate_query)
    workflow.add_node("searcher", search_node)
    workflow.add_node("dispatcher", dispatch_node)
    workflow.add_node("processor", process_node)
    workflow.add_node("storer", store_node)
    workflow.add_node("reporter", report_node)
    
    # Define Edges
    workflow.set_entry_point("translator")
    workflow.add_edge("translator", "searcher")
    workflow.add_edge("searcher", "dispatcher")
    
    workflow.add_conditional_edges(
        "dispatcher",
        should_continue,
        {
            "processor": "processor",
            "reporter": "reporter"
        }
    )
    
    workflow.add_edge("processor", "storer")
    workflow.add_edge("storer", "dispatcher")
    workflow.add_edge("reporter", END)
    
    return workflow.compile()
