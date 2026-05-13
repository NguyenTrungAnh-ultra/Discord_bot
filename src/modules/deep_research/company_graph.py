from langgraph.graph import StateGraph, END
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.company_nodes.profile_builder import build_profile
from src.modules.deep_research.company_nodes.financial_auditor import audit_finances
from src.modules.deep_research.company_nodes.company_storer import store_company_data
from src.modules.deep_research.company_nodes.report_synthesizer import synthesize_report
from src.modules.deep_research.company_nodes.cache_checker import check_cache

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
    # Chạy tuần tự: 0 -> 1 -> 2 -> 3 -> 4
    workflow.set_entry_point("cache_checker")
    workflow.add_edge("cache_checker", "profile_builder")
    workflow.add_edge("profile_builder", "financial_auditor")
    workflow.add_edge("financial_auditor", "company_storer")
    workflow.add_edge("company_storer", "report_synthesizer")
    workflow.add_edge("report_synthesizer", END)

    return workflow.compile()
