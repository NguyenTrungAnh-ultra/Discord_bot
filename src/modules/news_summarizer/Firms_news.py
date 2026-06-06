import os
from src.core.db.connection import Database
from src.modules.news_summarizer.scanners.tin_doanh_nghiep import VCI_news
import discord
from dotenv import load_dotenv
from vnstock import Trading

# Config
trading = Trading(source='VCI') 

# TOOLS

def _status(tickers: list):
    df = trading.price_board(symbols_list=tickers)
    df = df[[('listing', 'symbol'), ('listing', 'ref_price'), ('match', 'match_price'), ('match', 'accumulated_volume')]]
    df.columns = df.columns.droplevel(0)
    df['diff'] = round(((df['match_price'] - df['ref_price'])/df['ref_price'])*100, 2)
    df['match_price'] = round(df['match_price']/1000, 2)
    df['up_down_same'] = [
                            'ceiling' if 6.7 <= x <= 7.1 else 
                            'floor' if -7.1 <= x <= -6.7 else 
                            'up' if x > 0 else 
                            'down' if x < 0 else 
                            'same' 
                            for x in df['diff']
                        ]
    df = df.set_index('symbol')
    df = df[['match_price', 'accumulated_volume', 'diff', 'up_down_same']]
    return df


#__________________________________MAIN______________________________________________________________________________
def main():
    load_dotenv()
    webhook_url = os.getenv('WEBHOOK_URL_TIN_TUC')
    
    if not webhook_url:
        print("Lỗi: Chưa cài đặt DISCORD_WEBHOOK_URL")
        return

    # Khởi tạo webhook
    webhook = discord.SyncWebhook.from_url(webhook_url)
    #############################################################################################################
    # Lấy tin từ API
    news_tool = VCI_news()
    current_news_list = news_tool.get_news(page=1, page_size=99)
    if not current_news_list:
        print("Không lấy được dữ liệu từ API.")
        return
    current_tickers = list(set([x.get('ticker') for x in current_news_list]))
    # Lấy status các mã
    status = _status(current_tickers)

    # Lấy lịch sử id đã gửi từ Database (2 ngày gần nhất)
    query_sent = "SELECT id FROM news WHERE update_date >= CURRENT_DATE - INTERVAL '2 days'"
    try:
        sent_records = Database.execute_query(query_sent, fetch=True)
        sent_ids = [r['id'] for r in sent_records]
    except Exception as e:
        print(f"Lỗi khi lấy lịch sử từ DB: {e}")
        sent_ids = []
    
    print(f"Đã lấy {len(current_news_list)} tin từ API. Lịch sử DB (2 ngày) có {len(sent_ids)} tin.")

    count = 0
    
    # Duyệt ngược (reversed) để tin cũ nhất trong batch gửi trước, tin mới nhất gửi sau
    for item in reversed(current_news_list):
        # KIỂM TRA: Nếu tin chưa có trong danh sách đã gửi
        item_id = item.get('id')
        if item_id not in sent_ids:
            try:
                title = item.get('news_title', 'Không tiêu đề')
                ticker = item.get('ticker')
                link = item.get('news_source_link', '#')
                source = item.get('news_from_name', 'VCI')
                time_str = item.get('update_date')
                sentiment = item.get('sentiment')
                short_content = item.get('news_short_content')
                tiker_status = status.loc[ticker]
                
                print(f"--> Gửi tin mới: {title}")
                
            # Gửi Webhook
                # Màu vang
                HEX_COLOR_VANG = 0xFF9900
                # Màu Đỏ đậm
                HEX_COLOR_DO = 0xEE0000
                # Màu Xanh lá (Green)
                HEX_COLOR_XANH_LA = 0x00FF00

                # Define Emoji for Footer based on stock status
                status_emoji_map = {
                    'ceiling': '🟣', 
                    'floor': '🔵', 
                    'up': '🟢', 
                    'down': '🔴', 
                    'same': '🟡'
                }
                emoji = status_emoji_map.get(tiker_status['up_down_same'], '⚪')
                
                # Format description
                description = f"{short_content}\n\n**{emoji} {tiker_status['diff']}%** | **{tiker_status['match_price']}** | Vol: **{tiker_status['accumulated_volume']:,}**"

                # Choose Color based on Sentiment
                if sentiment == 'Positive':
                    embed_color = HEX_COLOR_XANH_LA
                elif sentiment == 'Negative':
                    embed_color = HEX_COLOR_DO
                else:
                    embed_color = HEX_COLOR_VANG

                # Tạo Embed
                embed = discord.Embed(
                    title=f"🔥 {title}", 
                    description=description,
                    url=link, 
                    color=embed_color
                )
                embed.set_footer(text=f"Nguồn: {source} | Thời gian: {time_str}")
                
                # Gửi Embed
                webhook.send(embed=embed)
                
                # Lưu vào Database sau khi gửi thành công
                insert_query = """
                    INSERT INTO news (id, news_title, ticker, news_source_link, news_from_name, update_date, sentiment, news_short_content, slug)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
                Database.execute_query(insert_query, (
                    item_id, title, ticker, link, source, time_str, sentiment, short_content, item.get('slug')
                ))
                
                count += 1
                
            except Exception as e:
                print(f"Lỗi khi xử lý tin {item_id}: {e}")
        else:
            # print(f"Tin đã tồn tại, bỏ qua: {item.get('news_title')}")
            pass

    if count > 0:
        print(f"Đã gửi và lưu {count} tin mới vào Database.")
    else:
        print("Không có tin mới so với Database.")

if __name__ == "__main__":
    main()
