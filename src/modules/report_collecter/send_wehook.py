"""
Discord Webhook Sender - Today's Reports with PDF Download
Quét tất cả sources, tải PDF và gửi báo cáo doanh nghiệp/ngành TRONG NGÀY
"""

import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
import requests
from datetime import datetime, date, timezone
from typing import List, Dict, Set
import json
import re
from pathlib import Path

load_dotenv()
WEBHOOK = os.getenv('BAO_CAO_DOANH_NGHIEP')

# Config
SENT_FILE = r".\temp\reports\sent_reports.json"
MAX_REPORTS = 20  # Limit
PDF_CACHE_DIR = r".\temp\reports\pdf_cache"


class TodayReportSender:
    """Gửi báo cáo TRONG NGÀY với PDF attachment"""
    
    def __init__(self):
        self.sent = self._load_sent()
        self.today = date.today()
        os.makedirs(PDF_CACHE_DIR, exist_ok=True)
        
        # Sources (path, color)
        self.sources = {
            'VCBS-DN': (r'.\temp\reports\VCBS\bao_cao_doanh_nghiep\vcbs_reports.csv', 0x00aa00),
            'VCBS-Ngành': (r'.\temp\reports\VCBS\bao_cao_nganh\vcbs_reports.csv', 0x00ff00),
            'ACBS-DN': (r'.\temp\reports\ACBS\bao_cao_doanh_nghiep\acbs_reports.csv', 0x0099ff),
            'KBSV-DN': (r'.\temp\reports\KBSV\bao_cao_cong_ty\kbsv_reports.csv', 0xff6600),
            'KBSV-Ngành': (r'.\temp\reports\KBSV\bao_cao_nganh\kbsv_reports.csv', 0xff9933),
            'SSI': (r'.\temp\reports\SSI\ban_tin_thi_truong\ssi_reports.csv', 0xff0066),
        }
        
    def _load_sent(self) -> Set[str]:
        if os.path.exists(SENT_FILE):
            try:
                with open(SENT_FILE, 'r') as f:
                    return set(json.load(f).get('sent_report_ids', []))
            except:
                pass
        return set()
    
    def _save_sent(self):
        os.makedirs(os.path.dirname(SENT_FILE), exist_ok=True)
        with open(SENT_FILE, 'w') as f:
            json.dump({'sent_report_ids': list(self.sent), 'updated': datetime.now().isoformat()}, f)
    
    def _is_today(self, date_str):
        """Check if date is YESTERDAY (for daily morning reports)"""
        try:
            if pd.isna(date_str) or not date_str:
                return False
            
            # Parse DD/MM/YYYY format
            report_date = pd.to_datetime(date_str, format='%d/%m/%Y', errors='coerce')
            if pd.isna(report_date):
                return False
            
            # Convert self.today (date) to Timestamp for comparison
            today_ts = pd.Timestamp(self.today)
            
            # Check if date is YESTERDAY
            days_diff = (today_ts - report_date).days
            return days_diff == 1  # Only yesterday
            
        except Exception as e:
            print(f"Date parse error: {e}")
            return False
    
    def get_today_reports(self) -> List[Dict]:
        """Get reports from YESTERDAY"""
        reports = []
        yesterday = (self.today - pd.Timedelta(days=1)).strftime('%d/%m/%Y')
        print(f"🔍 Scanning for YESTERDAY ({yesterday})...")
        
        for source, (path, color) in self.sources.items():
            if not os.path.exists(path):
                continue
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
                
                # Safety check for required columns
                if 'report_id' not in df.columns:
                    # Generate report_id if missing
                    df['report_id'] = df.apply(lambda row: f"{source}_{row.name}", axis=1)
                
                df = df[~df['report_id'].isin(self.sent)]
                
                # IMPORTANT: Skip if no date column (can't filter by date)
                if 'date' not in df.columns:
                    print(f"  ⚠️ {source}: No date column, skipping")
                    continue
                
                df = df[df['date'].apply(self._is_today)]
                
                for _, row in df.iterrows():
                    r = row.to_dict()
                    r['source'] = source
                    r['color'] = color
                    reports.append(r)
                
                if len(df) > 0:
                    print(f"  ✅ {source}: {len(df)}")
            except Exception as e:
                print(f"  ❌ {source}: {e}")
        
        return reports
    
    def download_pdf(self, report: Dict) -> str:
        """Download PDF, return path"""
        pdf_url = report.get('pdf_url') or report.get('download_url') or report.get('detail_url')
        
        print(f"    🔍 Checking PDF: {pdf_url}")
        
        if not pdf_url or not isinstance(pdf_url, str) or 'http' not in pdf_url:
            print(f"    ⚠️ Invalid PDF URL")
            return None
        
        # Generate filename
        ticker_raw = report.get('ticker', 'report')
        ticker = str(ticker_raw)[:10] if ticker_raw and not pd.isna(ticker_raw) else 'report'
        title_safe = re.sub(r'[^\w\s-]', '', report.get('title', ''))[:50]
        filename = f"{ticker}_{title_safe}_{report['report_id'][:8]}.pdf"
        filepath = os.path.join(PDF_CACHE_DIR, filename)
        
        # Check cache
        if os.path.exists(filepath):
            print(f"    ✅ Using cached PDF")
            return filepath
        
        # Download with cookies support
        try:
            # Load cookies from KBSV scraper if exists
            import pickle
            cookie_file = './temp/kbsv_cookies.pkl'
            session = requests.Session()
            
            if os.path.exists(cookie_file):
                try:
                    with open(cookie_file, 'rb') as f:
                        session.cookies.update(pickle.load(f))
                    print(f"    🍪 Loaded cookies")
                except:
                    pass
            
            # Try pdf_url first
            if pdf_url and '.pdf' in pdf_url.lower():
                print(f"    📥 Downloading PDF...")
                resp = session.get(pdf_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    print(f"    ✅ Downloaded PDF ({len(resp.content)//1024}KB)")
                    return filepath
                else:
                    print(f"    ❌ Download failed: status={resp.status_code}, size={len(resp.content)}")
        except Exception as e:
            print(f"    ❌ PDF download error: {e}")
        
        return None
    
    def send_report(self, report: Dict) -> bool:
        """Send single report with PDF"""
        if not WEBHOOK:
            return False
        
        ticker_raw = report.get('ticker', '')
        ticker = str(ticker_raw).upper() if ticker_raw and not pd.isna(ticker_raw) else ''
        title = report.get('title', 'Báo cáo')[:200]
        
        # Format title
        if ticker and len(ticker) >= 3:
            display_title = f"**[{ticker}]** {title}"
        else:
            display_title = title
        
        # Build embed
        embed = {
            'title': display_title[:256],
            'color': report.get('color', 0x808080),
            'fields': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),  # UTC timezone for Discord
            'footer': {'text': report['source']}
        }
        
        if ticker:
            embed['fields'].append({'name': '📊 Mã', 'value': f"**{ticker}**", 'inline': True})
        if report.get('date'):
            embed['fields'].append({'name': '📅 Ngày', 'value': report['date'], 'inline': True})
        
        # Links
        links = []
        if report.get('detail_url'):
            links.append(f"[📄 Chi tiết]({report['detail_url']})")
        if links:
            embed['fields'].append({'name': '🔗 Link', 'value': ' | '.join(links), 'inline': False})
        
        # Download PDF
        pdf_path = self.download_pdf(report)
        
        # Prepare payload
        payload = {
            'username': '📊 Report Bot',
            'embeds': [embed]
        }
        
        files = {}
        if pdf_path and os.path.exists(pdf_path):
            files = {'file': open(pdf_path, 'rb')}
            payload['content'] = f"📄 **PDF attached**"
        
        try:
            resp = requests.post(WEBHOOK, data={'payload_json': json.dumps(payload)}, files=files, timeout=15)
            
            if files:
                files['file'].close()
            
            if resp.status_code in [200, 204]:
                self.sent.add(report['report_id'])
                return True
            else:
                print(f"    ❌ HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"    ❌ Error: {e}")
            if files:
                files['file'].close()
            return False
    
    def run(self):
        """Main"""
        yesterday = self.today - pd.Timedelta(days=1)
        print(f"\n{'='*60}")
        print(f"📊 Yesterday's Report Sender")
        print(f"📅 Yesterday: {yesterday.strftime('%d/%m/%Y')}")
        print(f"{'='*60}\n")
        
        reports = self.get_today_reports()
        
        if not reports:
            print("✨ No new reports from yesterday!\n")
            return
        
        print(f"\n📤 Sending {len(reports)} reports...\n")
        
        sent = 0
        for i, r in enumerate(reports[:MAX_REPORTS], 1):
            print(f"[{i}/{min(len(reports), MAX_REPORTS)}] {r.get('title', '')[:60]}")
            if self.send_report(r):
                sent += 1
                import time
                time.sleep(1.5)  # Rate limit
        
        self._save_sent()
        
        print(f"\n{'='*60}")
        print(f"✅ Sent {sent}/{len(reports)} reports")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    TodayReportSender().run()
