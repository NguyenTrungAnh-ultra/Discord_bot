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

    def filter_reports(self) -> List[Dict]:
        """
        Filter all reports from CSV that haven't been sent.
        """
        reports = []
        print(f"🔍 Scanning all reports to find unsent items...")
        
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
                    
                # ALWAYS generate stable ID from title for consistency, ignoring CSV's report_id
                import hashlib
                def generate_stable_id(row):
                    return hashlib.md5(str(row['title']).strip().encode('utf-8')).hexdigest()
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

                # No date filtering, just take everything from CSV
                matched_reports = df
                
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

    def run(self):
        print(f"🚀 Starting Report Sender (Unsent items only)")
        
        reports = self.filter_reports()
        
        if not reports:
            print("✨ No new reports found.")
            return 0

        # Global Deduplication by report_id (across all sources)
        unique_reports = []
        seen_batch_ids = set()
        for r in reports:
            if r['report_id'] not in seen_batch_ids:
                unique_reports.append(r)
                seen_batch_ids.add(r['report_id'])
        
        reports = unique_reports

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
    # Simply send everything that hasn't been sent yet
    sender.run() 
