import requests
from datetime import datetime, timedelta
from core.utils.user_agent import get_headers
class VCI_news:
    def __init__(self):
        self.url = "https://ai.vietcap.com.vn/api/v2/news_info"
        self.headers = get_headers(data_source='VCI')

    def _request_news(self, page=1, page_size=12, start_date=None, end_date=None) -> dict:
        if start_date is None:
            start_date = str(datetime.today().strftime('%Y-%m-%d'))
        if end_date is None:
            end_date = str(datetime.today().strftime('%Y-%m-%d'))

        params = {
            "page": page,
            "page_size": page_size, 
            "update_from": start_date, 
            "update_to": end_date,     
            "language": "vi",
            "ticker": "",
            "industry": "",
            "sentiment": "",
            "newsfrom": ""
        }
        try:
            response = requests.request("GET", url=self.url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f'Request lỗi: {e}')
            return {}

    def _fetch_and_filter_news(self, raw_meat: dict) -> list:
        needed_keys = ['id', 'news_title', 'update_date', 'news_from_name', 'news_source_link']

        if not raw_meat or 'news_info' not in raw_meat:
            return []

        filtered_list = [
            {key: item[key] for key in needed_keys if key in item}
            for item in raw_meat.get('news_info', [])
        ]
        return filtered_list

    def get_news(self, page=1, page_size=12, start_date=None, end_date=None):
        raw_data = self._request_news(page=page, 
                                      page_size=page_size, 
                                      start_date=start_date, 
                                      end_date=end_date)
        return self._fetch_and_filter_news(raw_data)