from News.config import DATA_FILE
import json

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    news = json.load(f)
    news_dict_by_title = {item['title']: item['link'] for item in news}
    for key, val in news_dict_by_title.items():
        print(key, val, '\n')