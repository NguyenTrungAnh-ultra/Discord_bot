from langgraph.graph import StateGraph, END
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.company_nodes.profile_builder import build_profile
from src.modules.deep_research.company_nodes.financial_auditor import audit_finances
from src.modules.deep_research.company_nodes.company_storer import store_company_data
from src.modules.deep_research.company_nodes.report_synthesizer import synthesize_report
from src.modules.deep_research.company_nodes.cache_checker import check_cache

def route_after_cache(state: CompanyState):
    if state.get("profile_from_cache") and state.get("finance_from_cache"):
        print("-> [Routing] Fully cached. Jumping to report_synthesizer.")
        return "report_synthesizer"
    elif state.get("profile_from_cache"):
        print("-> [Routing] Profile cached. Jumping to financial_auditor.")
        return "financial_auditor"
    else:
        print("-> [Routing] Profile missing. Proceeding to profile_builder.")
        return "profile_builder"

def route_after_profile(state: CompanyState):
    if state.get("finance_from_cache"):
        print("-> [Routing] Finance already cached. Jumping to company_storer.")
        return "company_storer"
    else:
        print("-> [Routing] Finance missing. Proceeding to financial_auditor.")
        return "financial_auditor"

def create_company_graph():
    """
    Khởi tạo luồng xử lý (Graph) cho phân tích doanh nghiệp.
    """
    workflow = StateGraph(CompanyState)

    # Thêm các Node
    workflow.add_node("cache_checker", check_cache)
    workflow.add_node("profile_builder", build_profile)
    workflow.add_node("financial_auditor", audit_finances)
    workflow.add_node("company_storer", store_company_data)
    workflow.add_node("report_synthesizer", synthesize_report)

    # Định nghĩa luồng (Edges)
    workflow.set_entry_point("cache_checker")
    
    workflow.add_conditional_edges(
        "cache_checker",
        route_after_cache,
        {
            "profile_builder": "profile_builder",
            "financial_auditor": "financial_auditor",
            "report_synthesizer": "report_synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "profile_builder",
        route_after_profile,
        {
            "financial_auditor": "financial_auditor",
            "company_storer": "company_storer"
        }
    )

    workflow.add_edge("financial_auditor", "company_storer")
    workflow.add_edge("company_storer", "report_synthesizer")
    workflow.add_edge("report_synthesizer", END)

    return workflow.compile()
