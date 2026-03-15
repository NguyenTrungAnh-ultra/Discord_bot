"""
Discord Webhook Sender - Fast & Stable
Gửi báo cáo mới với link PDF trực tiếp (không tải file).
"""

import os
from dotenv import load_dotenv
import pandas as pd
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Set
import json
import time
import urllib.parse

load_dotenv()
WEBHOOK = os.getenv('BAO_CAO_DOANH_NGHIEP')

# Config
SENT_FILE = os.path.join(os.getcwd(), "temp", "reports", "sent_reports.json")
MAX_REPORTS_PER_RUN = 30  # Increased limit since no file upload
RATE_LIMIT = 1.0  # Seconds between messages

class ReportSender:
    def __init__(self):
        self.sent_ids = self._load_sent()
        self.today = date.today()
        
        # Sources configuration
        base_path = os.getcwd()
        self.sources = {
            'VCBS-DN': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_doanh_nghiep', 'vcbs_reports.csv'),
            'VCBS-Ngành': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_nganh', 'vcbs_reports.csv'),
            'ACBS': os.path.join(base_path, 'temp', 'reports', 'ACBS', 'acbs_reports.csv'),
            'KBSV-DN': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_cong_ty', 'kbsv_reports.csv'),
            'KBSV-Ngành': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_nganh', 'kbsv_reports.csv'),
        }
        
    def _load_sent(self) -> Set[str]:
        if os.path.exists(SENT_FILE):
            try:
                with open(SENT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('sent_report_ids', []))
            except:
                pass
        return set()
    
    def _save_sent(self):
        os.makedirs(os.path.dirname(SENT_FILE), exist_ok=True)
        try:
            with open(SENT_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'sent_report_ids': list(self.sent_ids),
                    'updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving sent cache: {e}")

    def filter_reports(self, lookback_days: int = 1) -> List[Dict]:
        """
        Filter reports from the last N days.
        lookback_days=1 means today + yesterday (last 24h effectively).
        """
        reports = []
        target_dates = set()
        
        # Calculate target dates (Including TODAY)
        for i in range(0, lookback_days + 1):
            d = self.today - timedelta(days=i)
            target_dates.add(pd.Timestamp(d).strftime('%d/%m/%Y'))
            target_dates.add(pd.Timestamp(d).strftime('%Y-%m-%d'))
            
        print(f"🔍 Scanning reports for dates: {sorted(list(target_dates))}")
        
        for source_name, csv_path in self.sources.items():
            if not os.path.exists(csv_path):
                # print(f"  ⚠️ Missing CSV: {csv_path}")
                continue
                
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                
                # Normalize columns
                if 'pdf_url' not in df.columns and 'link' in df.columns:
                    df['pdf_url'] = df['link']
                
                # Check required columns
                required = ['title', 'date', 'pdf_url']
                if not all(col in df.columns for col in required):
                    continue
                    
                # Generate stable ID if missing (using MD5 instead of hash for stability)
                if 'report_id' not in df.columns:
                    import hashlib
                    def generate_stable_id(row):
                        raw_str = str(row['title']) + str(row['date'])
                        return f"{source_name}_{hashlib.md5(raw_str.encode()).hexdigest()}"
                    df['report_id'] = df.apply(generate_stable_id, axis=1)
                
                # Filter by date
                # Normalize date format in CSV to DD/MM/YYYY for comparison
                # (Simple string match is faster and safer than parsing all formats)
                
                # Helper to normalize date string from CSV
                def normalize_date(d):
                    if pd.isna(d): return ''
                    d = str(d).strip()
                    # If YYYY-MM-DD
                    if '-' in d and d.split('-')[0].isdigit() and len(d.split('-')[0]) == 4:
                        try:
                            return datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except: pass
                    return d

                matched_reports = df[df['date'].apply(normalize_date).isin(target_dates)]
                
                # Filter duplicates in the dataframe itself just in case
                matched_reports = matched_reports.drop_duplicates(subset=['report_id'])

                # Filter already sent
                new_reports = matched_reports[~matched_reports['report_id'].isin(self.sent_ids)]
                
                for _, row in new_reports.iterrows():
                    reports.append({
                        'source': source_name,
                        'title': row['title'],
                        # 'ticker': row.get('ticker', ''),
                        'date': row['date'],
                        'pdf_url': row['pdf_url'],
                        'report_id': row['report_id']
                    })
                    
                if not new_reports.empty:
                    print(f"  ✅ {source_name}: Found {len(new_reports)} new reports")
                    
            except Exception as e:
                print(f"  ❌ Error reading {source_name}: {e}")
                
        return reports

    def send_to_discord(self, report: Dict) -> bool:
        if not WEBHOOK:
            print("❌ Discord Webhook URL not set!")
            return False
            
        # Customize content
        source = report['source']
        title = report['title']
        date_str = str(report['date'])
        raw_pdf_url = report['pdf_url']
        # ticker = report.get('ticker', '')
        
        # if pd.isna(ticker): ticker = ''

        # Encode URL for Discord (handle spaces and unicode)
        pdf_url = raw_pdf_url
        if pdf_url and str(pdf_url).startswith('http'):
            try:
                # Split into base and path to encode path properly
                parts = urllib.parse.urlsplit(pdf_url)
                # Encode path, query, fragment
                encoded_path = urllib.parse.quote(parts.path)
                encoded_query = urllib.parse.quote(parts.query, safe="=&")
                pdf_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, encoded_query, parts.fragment))
            except:
                pass # Keep original if error
        
        # Embed structure
        embed = {
            "title": title,
            "url": pdf_url if pdf_url and str(pdf_url).startswith('http') else None,
            "description": f"[👉 Xem chi tiết tại đây]({pdf_url})",
            "color": 5763719,  # Green (0x57F287)
            "author": {
                "name": f"Báo cáo mới từ {source}",
            },
            "footer": {
                "text": f"📅 Cập nhật: {date_str}"
            }
        }
        
        # Custom title formatting (removed ticker as requested)
        # if ticker and len(str(ticker)) < 10:
        #     embed["title"] = f"[{ticker}] {title}"
            
        payload = {
            "username": "Stock Report Bot",
            "embeds": [embed]
        }
        
        try:
            resp = requests.post(WEBHOOK, json=payload, timeout=10)
            if resp.status_code in [200, 204]:
                self.sent_ids.add(report['report_id'])
                return True
            else:
                print(f"    ❌ Failed to send: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"    ❌ Network error: {e}")
            return False

    def run(self, lookback_days=1):
        print(f"🚀 Starting Report Sender (Lookback: {lookback_days} days)")
        
        reports = self.filter_reports(lookback_days=lookback_days)
        
        if not reports:
            print("✨ No new reports found.")
            return 0

        print(f"📤 Preparing to send {len(reports)} reports...")
        
        count = 0
        for i, report in enumerate(reports):
            if count >= MAX_REPORTS_PER_RUN:
                print(f"⚠️ Reached limit of {MAX_REPORTS_PER_RUN} reports per run.")
                break
                
            print(f"[{i+1}/{len(reports)}] Sending: {report['title'][:50]}...")
            if self.send_to_discord(report):
                count += 1
                time.sleep(RATE_LIMIT)
            else:
                print(f"    Skipping...")
        
        self._save_sent()
        print(f"✅ Completed! Sent {count} reports.")
        return count

if __name__ == "__main__":
    sender = ReportSender()
    # Default to 1 day for production
    sender.run(lookback_days=1) 
