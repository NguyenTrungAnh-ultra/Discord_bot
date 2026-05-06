"""
Discord Webhook Sender - Fast & Stable
Gửi báo cáo mới với link PDF trực tiếp từ Database.
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
import hashlib
from src.core.db import Database

load_dotenv()
WEBHOOK = os.getenv('BAO_CAO_DOANH_NGHIEP')

# Config
MAX_REPORTS_PER_RUN = 30
RATE_LIMIT = 1.0

class ReportSender:
    def __init__(self):
        self.today = date.today()
        base_path = os.getcwd()
        self.sources = {
            'VCBS-DN': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_doanh_nghiep', 'vcbs_reports.csv'),
            'VCBS-Ngành': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_nganh', 'vcbs_reports.csv'),
            'ACBS': os.path.join(base_path, 'temp', 'reports', 'ACBS', 'acbs_reports.csv'),
            'KBSV-DN': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_cong_ty', 'kbsv_reports.csv'),
            'KBSV-Ngành': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_nganh', 'kbsv_reports.csv'),
        }

    def sync_csv_to_db(self):
        print(f"🔄 Syncing CSV reports to Database...")
        for source_name, csv_path in self.sources.items():
            if not os.path.exists(csv_path):
                continue
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                if 'pdf_url' not in df.columns and 'link' in df.columns:
                    df['pdf_url'] = df['link']
                required = ['title', 'date', 'pdf_url']
                if not all(col in df.columns for col in required):
                    continue
                for _, row in df.iterrows():
                    title = str(row['title']).strip()
                    report_id = hashlib.md5(title.encode('utf-8')).hexdigest()
                    insert_query = "INSERT INTO report (report_id, title, date, pdf_url, company, report_type, ticker, is_sent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (report_id) DO NOTHING"
                    company = row.get('company', source_name)
                    report_type = row.get('report_type', 'Company' if 'DN' in source_name else 'Industry')
                    ticker = row.get('ticker', '')
                    raw_date = row['date']
                    try:
                        if isinstance(raw_date, str) and '/' in raw_date:
                            d_parts = raw_date.split('/')
                            if len(d_parts) == 3: raw_date = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}"
                    except: raw_date = None
                    Database.execute_query(insert_query, (report_id, title, raw_date, row['pdf_url'], company, report_type, ticker, False))
            except Exception as e:
                print(f"  ❌ Error syncing {source_name}: {e}")

    def get_unsent_reports(self) -> List[Dict]:
        query = "SELECT * FROM report WHERE is_sent = FALSE LIMIT %s"
        return Database.execute_query(query, (MAX_REPORTS_PER_RUN,), fetch=True)

    def mark_as_sent(self, report_id: str):
        query = "UPDATE report SET is_sent = TRUE WHERE report_id = %s"
        Database.execute_query(query, (report_id,))

    def send_to_discord(self, report: Dict) -> bool:
        if not WEBHOOK: return False
        title, date_val, pdf_url = report['title'], report['date'], report['pdf_url']
        date_str = date_val.strftime('%d/%m/%Y') if hasattr(date_val, 'strftime') else str(date_val)
        source = report['company'] or "Báo cáo"
        if pdf_url and str(pdf_url).startswith('http'):
            try:
                p = urllib.parse.urlsplit(pdf_url)
                pdf_url = urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(p.path), urllib.parse.quote(p.query, safe="=&"), p.fragment))
            except: pass
        embed = {"title": title, "url": pdf_url if pdf_url and str(pdf_url).startswith('http') else None, "description": f"[👉 Xem chi tiết tại đây]({pdf_url})", "color": 5763719, "author": {"name": f"Báo cáo mới từ {source}"}, "footer": {"text": f"📅 Ngày: {date_str}"}}
        try:
            resp = requests.post(WEBHOOK, json={"username": "Stock Report Bot", "embeds": [embed]}, timeout=10)
            return resp.status_code in [200, 204]
        except: return False

    def run(self):
        print(f"🚀 Starting Database-backed Report Sender")
        self.sync_csv_to_db()
        reports = self.get_unsent_reports()
        if not reports:
            print("✨ No new reports to send.")
            return 0
        print(f"📤 Preparing to send {len(reports)} reports from DB...")
        count = 0
        for i, report in enumerate(reports):
            print(f"[{i+1}/{len(reports)}] Sending: {report['title'][:50]}...")
            if self.send_to_discord(report):
                self.mark_as_sent(report['report_id'])
                count += 1
                time.sleep(RATE_LIMIT)
            else: print(f"    Skipping...")
        print(f"✅ Completed! Sent {count} reports.")
        return count

if __name__ == "__main__":
    ReportSender().run()
