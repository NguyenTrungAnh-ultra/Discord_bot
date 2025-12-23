import os
from News.tool import load_history, update_history
from News.tin_doanh_nghiep import VCI_news
from datetime import datetime
import discord
from dotenv import load_dotenv
from vnstock import Trading

# Config
HISTORY_FILE = "/app/source/requested_news.json" 
today = str(datetime.today().strftime('%Y-%m-%d'))
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
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    # webhook_url = 'https://discord.com/api/webhooks/1452905466693685299/yCdvoSw8_sYWsRGqq8zdw1iNq3l2Ts4FEK3u7jtrP6Od4D2_DMkIqYlaVQf5jT7ClEZH'
    
    if not webhook_url:
        print("Lỗi: Chưa cài đặt DISCORD_WEBHOOK_URL")

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

    # Lấy lịch sử id đã gửi
    histories = load_history(direct=HISTORY_FILE)
    sent_ids = [x.get('id') for x in histories]
    
    print(f"Đã lấy {len(current_news_list)} tin từ API. Lịch sử đang lưu {len(sent_ids)} tin.")

    count = 0
    # Tạo danh sách mới sẽ lưu lại (bắt đầu bằng danh sách cũ)
    updated_history = histories.copy()
    
    # Duyệt ngược (reversed) để tin cũ nhất trong batch gửi trước, tin mới nhất gửi sau
    for item in reversed(current_news_list):
        # KIỂM TRA: Nếu tin chưa có trong danh sách đã gửi
        if item.get('id') not in sent_ids:
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
                
                # Format Footer
                footer_text = f"{emoji} {tiker_status['diff']}% | {tiker_status['match_price']} | Vol: {tiker_status['accumulated_volume']:,}"

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
                    description=f"{short_content}\nNguồn: **{source}**\nThời gian: **{time_str}**",
                    url=link, 
                    color=embed_color
                )
                embed.set_footer(text=footer_text)
                
                # Gửi Embed
                webhook.send(embed=embed)
                ##########################################################################
                # print(f"🔥 **{title}**\nNguồn: {source} ({time_str})\n{link}")
                
                # Đánh dấu là đã gửi bằng cách thêm vào danh sách temp (chèn vào đầu list để giữ tính mới nhất)
                updated_history.insert(0, item)
                count += 1
                
            except Exception as e:
                print(f"Lỗi khi gửi tin: {e}")
        else:
            # print(f"Tin đã tồn tại, bỏ qua: {item.get('news_title')}")
            pass

    # Lưu lại trạng thái mới vào JSON
    if count > 0:
        update_history(_list = updated_history, direct=HISTORY_FILE)
        print(f"Đã gửi và lưu {count} tin mới.")
    else:
        print("Không có tin mới so với file lưu trữ.")

if __name__ == "__main__":
    main()
