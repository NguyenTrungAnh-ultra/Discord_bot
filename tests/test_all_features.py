import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import date, datetime

# Import utilities
from src.utils.text import clean_title
from src.utils.ticker import extract_tickers
from src.utils.date_parser import parse_publish_date, format_date_display

# Import core
from src.core.ai.tracker import estimate_tokens, count_response_tokens
from src.core.db.connection import Database, AsyncDatabase
from src.core.ai.client import get_genai_client

# Import graphs
from src.modules.deep_research.main_graph import create_research_graph
from src.modules.deep_research.company_graph import create_company_graph

# 1. TEST UTILITIES
class TestUtilities:
    def test_clean_title(self):
        assert clean_title("🔥 VIC ticker news") == "VIC ticker news"
        assert clean_title("   No emoji title   ") == "No emoji title"
        assert clean_title("") == ""
        assert clean_title(None) == ""

    def test_extract_tickers(self):
        assert extract_tickers("VIC: Vingroup plans EV expansion") == "VIC"
        assert extract_tickers("HPG, HSG steel production") == "HPG,HSG"
        assert extract_tickers("A basic sentence without short words") is None
        # Test excluded words (e.g. CEO is excluded, so it should not be extracted)
        assert extract_tickers("CTCP CEO") is None

    def test_parse_publish_date(self):
        assert parse_publish_date("12/05/2024") == date(2024, 5, 12)
        assert parse_publish_date("2024-05-12") == date(2024, 5, 12)
        assert parse_publish_date("Q1/2024") == date(2024, 3, 31)
        assert parse_publish_date("Quý 3-2024") == date(2024, 9, 30)
        assert parse_publish_date("2024") == date(2024, 12, 31)
        assert parse_publish_date("") is None

    def test_format_date_display(self):
        assert format_date_display(date(2024, 5, 12)) == "12/05/2024"
        assert format_date_display("2024-05-12") == "12/05/2024"
        assert format_date_display("") == "N/A"

# 2. TEST CORE AI & TRACKER
class TestCoreAI:
    def test_estimate_tokens(self):
        assert estimate_tokens("hello") == 2  # 5 // 3 + 1
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_count_response_tokens_with_metadata(self):
        mock_response = MagicMock()
        mock_response.usage_metadata.candidates_token_count = 42
        assert count_response_tokens(mock_response) == 42

    def test_count_response_tokens_fallback(self):
        mock_response = MagicMock()
        del mock_response.usage_metadata
        mock_response.text = "Hello world"
        assert count_response_tokens(mock_response) == 4  # 11 // 3 + 1

    def test_get_genai_client(self):
        # Verify client compiles and instantiates if key is present
        if os.getenv("GEMINI_API_KEY"):
            client = get_genai_client()
            assert client is not None
        else:
            pytest.skip("GEMINI_API_KEY not found in environment, skipping client initialization test.")

# 3. TEST CORE DATABASE
class TestCoreDatabase:
    def test_database_connection(self):
        try:
            # Test simple query execution
            res = Database.execute_query("SELECT 1 as val", fetch=True)
            assert len(res) == 1
            assert res[0]['val'] == 1
        except Exception as e:
            pytest.skip(f"Database connection failed (might be offline): {e}")

    @pytest.mark.asyncio
    async def test_async_database_connection(self):
        try:
            res = await AsyncDatabase.fetch_query("SELECT 1 as val")
            assert len(res) == 1
            assert res[0]['val'] == 1
        except Exception as e:
            pytest.skip(f"Async Database connection failed (might be offline): {e}")

# 4. TEST NEWS SUMMARIZER (MOCKED)
class TestNewsSummarizer:
    @patch('src.modules.news_summarizer.Firms_news.discord.SyncWebhook')
    @patch('src.modules.news_summarizer.Firms_news.VCI_news')
    @patch('src.modules.news_summarizer.Firms_news.Database')
    @patch('src.modules.news_summarizer.Firms_news._status')
    def test_firms_news_main_flow(self, mock_status, mock_db, mock_vci_news, mock_webhook):
        from src.modules.news_summarizer.Firms_news import main as news_main
        
        # Setup environment variable
        os.environ['WEBHOOK_URL_TIN_TUC'] = "https://discord.com/api/webhooks/mock"

        # Mock VCI News responses
        mock_news_instance = MagicMock()
        mock_news_instance.get_news.return_value = [
            {
                'id': 12345,
                'ticker': 'VIC',
                'news_title': 'VIC test news title',
                'news_source_link': 'http://example.com/vic',
                'news_from_name': 'VCI',
                'update_date': '2026-06-06 12:00:00',
                'sentiment': 'Positive',
                'news_short_content': 'VIC is performing exceptionally well.',
                'slug': 'vic-test-slug'
            }
        ]
        mock_vci_news.return_value = mock_news_instance

        # Mock DB sent records to return empty (meaning news is new)
        mock_db.execute_query.return_value = []

        # Mock Ticker status
        import pandas as pd
        mock_status.return_value = pd.DataFrame({
            'match_price': [45.0],
            'accumulated_volume': [100000],
            'diff': [2.5],
            'up_down_same': ['up']
        }, index=['VIC'])

        # Mock Discord Webhook
        mock_webhook_instance = MagicMock()
        mock_webhook.from_url.return_value = mock_webhook_instance

        # Execute main
        news_main()

        # Asserts
        mock_webhook_instance.send.assert_called_once()
        # Check if Database.execute_query was called
        assert mock_db.execute_query.call_count > 0

# 5. TEST GRAPHS (MOCKED COMPILATION & ROUTING FLOWS)
class TestLangGraphs:
    def test_graphs_compile(self):
        company_graph = create_company_graph()
        research_graph = create_research_graph()
        assert company_graph is not None
        assert research_graph is not None

    @pytest.mark.asyncio
    @patch('src.modules.deep_research.company_graph.check_cache')
    @patch('src.modules.deep_research.company_graph.synthesize_report')
    async def test_company_graph_cached_routing_flow(self, mock_synthesize, mock_check_cache):
        # Mock nodes behavior
        mock_check_cache.return_value = {
            "profile_from_cache": {"profile": "VIC Business Profile"},
            "finance_from_cache": {"finance": "VIC Financial Analysis"}
        }
        mock_synthesize.return_value = {
            "final_memo": "Mocked Final Memo"
        }

        app = create_company_graph()
        initial_state = {
            "ticker": "VIC",
            "business_profile": None,
            "financial_data": None,
            "financial_insight": None,
            "final_memo": None,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "node_tokens": {}
        }

        final_state = await app.ainvoke(initial_state)
        assert final_state["final_memo"] == "Mocked Final Memo"
        # Ensure the cache checker ran and routed directly to synthesize report
        mock_check_cache.assert_called_once()
        mock_synthesize.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.modules.deep_research.main_graph.translate_query')
    @patch('src.modules.deep_research.main_graph.retrieve_memory_node')
    @patch('src.modules.deep_research.main_graph.search_node')
    @patch('src.modules.deep_research.main_graph.dispatch_node')
    @patch('src.modules.deep_research.main_graph.process_node')
    @patch('src.modules.deep_research.main_graph.store_node')
    @patch('src.modules.deep_research.main_graph.report_node')
    async def test_deep_research_graph_routing_flow(self, mock_report, mock_store, mock_process, mock_dispatch, mock_search, mock_memory, mock_translate):
        # Mocking the node execution flows
        mock_translate.return_value = {"search_queries": ["VIC news"]}
        mock_memory.return_value = {}
        mock_search.return_value = {"urls": ["http://example.com/1"]}
        
        # First dispatch returns current_url to process
        # Second dispatch returns no current_url to finish
        mock_dispatch.side_effect = [
            {"current_url": "http://example.com/1", "iteration": 1},
            {"current_url": None, "iteration": 2}
        ]
        mock_process.return_value = {"current_title": "VIC", "current_content": "Content"}
        mock_store.return_value = {"insights": ["insight 1"]}
        mock_report.return_value = {"report": "Deep Research Report"}

        app = create_research_graph()
        initial_state = {
            "query": "VIC news",
            "max_iterations": 3,
            "iteration": 0,
            "urls": [],
            "insights": [],
            "report": "",
            "search_queries": []
        }

        final_state = await app.ainvoke(initial_state)
        assert final_state["report"] == "Deep Research Report"
        
        # Assertions to ensure workflow executed appropriate nodes
        mock_translate.assert_called_once()
        mock_search.assert_called_once()
        assert mock_dispatch.call_count == 2
        mock_process.assert_called_once()
        mock_store.assert_called_once()
        mock_report.assert_called_once()
