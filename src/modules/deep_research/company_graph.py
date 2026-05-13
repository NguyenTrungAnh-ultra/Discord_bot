from langgraph.graph import StateGraph, END
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.company_nodes.profile_builder import build_profile
from src.modules.deep_research.company_nodes.financial_auditor import audit_finances
from src.modules.deep_research.company_nodes.company_storer import store_company_data
from src.modules.deep_research.company_nodes.report_synthesizer import synthesize_report

def create_company_graph():
    """
    Khởi tạo luồng xử lý (Graph) cho phân tích doanh nghiệp.
    """
    workflow = StateGraph(CompanyState)

    # Thêm các Node
    workflow.add_node("profile_builder", build_profile)
    workflow.add_node("financial_auditor", audit_finances)
    workflow.add_node("company_storer", store_company_data)
    workflow.add_node("report_synthesizer", synthesize_report)

    # Định nghĩa luồng (Edges)
    # Chạy tuần tự: 1 -> 2 -> 3 -> 4
    workflow.set_entry_point("profile_builder")
    workflow.add_edge("profile_builder", "financial_auditor")
    workflow.add_edge("financial_auditor", "company_storer")
    workflow.add_edge("company_storer", "report_synthesizer")
    workflow.add_edge("report_synthesizer", END)

    return workflow.compile()
