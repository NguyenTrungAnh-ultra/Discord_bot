import json
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from core.utils.user_agent import get_headers

headers = get_headers(data_source='VCI')
url = "https://ai.vietcap.com.vn/api/v2/news_info"
format = "%Y-%m-%d %H:%M:%S"

def get_news_VCI(page, 
                 page_size,
                 start_date = str(datetime.today().strftime('%Y-%m-%d')), 
                 end_date = str(datetime.today().strftime('%Y-%m-%d'))
                 )->dict:
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
    response = requests.request("GET", url, headers=headers, params=params)
    return response

def fetch_and_filter_news(raw_meat: dict)->list:
        '''Raw_meat: file json chưa chỉnh sửa gì'''
        needed_keys = ['news_title', 'update_date', 'news_from_name', 'news_source_link']
        filtered_list = [
            {key: item[key] for key in needed_keys if key in item}
            for item in raw_meat
        ]
        return filtered_list

print(str(datetime.today().strftime('%Y-%m-%d')))

# with open('/Users/nguyentrunganhonichan/Documents/Discord_bot/News/tin_moi.json', 'r', encoding="utf-8") as p:
#     articals = pd.DataFrame(json.load(p))
#     print(articals)