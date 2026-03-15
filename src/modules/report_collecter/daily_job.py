"""
Daily Report Worker
Runs every morning at 07:00 (via main.py) to:
1. Run all scanners (ACBS, KBSV, VCBS)
2. Send reports to Discord (Lookback = 1 day / Yesterday)
3. If no reports sent, notify Discord "No new reports".
"""
import sys
import os
import time
import requests
from datetime import datetime

# Setup Paths
# Assuming this script is at src/modules/report_collecter/daily_job.py
# Root is ../../../
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.append(root_dir)

# Import Scanners
try:
    from src.modules.report_collecter.scanners import ACBS, KBSV, VCBS
    from src.modules.report_collecter.send_wehook import ReportSender, WEBHOOK
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def run_scanners():
    print("🔄 [Daily] Starting Scanners...")
    
    # ACBS
    try:
        ACBS.run()
    except Exception as e:
        print(f"❌ ACBS Failed: {e}")
        
    # KBSV (Company + Industry)
    try:
        KBSV.run(bao_cao_cong_ty_url=True) # Corporate
        KBSV.run(bao_cao_nganh_url=True)   # Industry
    except Exception as e:
        print(f"❌ KBSV Failed: {e}")
        
    # VCBS (Corporate + Industry)
    try:
        VCBS.run('bao_cao_doanh_nghiep')
        VCBS.run('bao_cao_nganh')
    except Exception as e:
        print(f"❌ VCBS Failed: {e}")

def notify_no_reports():
    if not WEBHOOK:
        return
        
    payload = {
        "username": "Stock Report Bot",
        "content": f"📅 **{datetime.now().strftime('%d/%m/%Y')}**: [Bot] Hôm qua không có báo cáo phân tích mới."
    }
    try:
        requests.post(WEBHOOK, json=payload, timeout=5)
        print("✅ Sent 'No Reports' notification.")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")

def job_daily_scan():
    print(f"⏰ [Daily Job] Started at {datetime.now()}")
    
    # 1. Run Scanners
    run_scanners()
    
    # 2. Send Reports (Yesterday)
    try:
        sender = ReportSender()
        # Simply send everything that hasn't been sent yet
        sent_count = sender.run()
        
        # 3. Notify if empty
        if sent_count == 0:
            print("📭 No reports sent. Sending notification...")
            notify_no_reports()
        else:
            print(f"🚀 Sent {sent_count} reports successfully.")
            
    except Exception as e:
        print(f"❌ Report Sender Failed: {e}")
        
    print(f"🏁 [Daily Job] Finished at {datetime.now()}")

if __name__ == "__main__":
    try:
        job_daily_scan()
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal Error in Daily Job: {e}")
        sys.exit(1)
