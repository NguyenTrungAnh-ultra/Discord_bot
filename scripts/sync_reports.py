
import os
import json
import pandas as pd
import hashlib

# Cấu hình đường dẫn
base_path = os.getcwd()
SENT_FILE = os.path.join(base_path, "temp", "reports", "sent_reports.json")
sources = {
    'VCBS-DN': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_doanh_nghiep', 'vcbs_reports.csv'),
    'VCBS-Ngành': os.path.join(base_path, 'temp', 'reports', 'VCBS', 'bao_cao_nganh', 'vcbs_reports.csv'),
    'ACBS': os.path.join(base_path, 'temp', 'reports', 'ACBS', 'acbs_reports.csv'),
    'KBSV-DN': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_cong_ty', 'kbsv_reports.csv'),
    'KBSV-Ngành': os.path.join(base_path, 'temp', 'reports', 'KBSV', 'bao_cao_nganh', 'kbsv_reports.csv'),
}

def sync_sent_reports():
    print("🔄 Đang bắt đầu đồng bộ hóa lịch sử gửi tin...")
    
    # Load lịch sử cũ
    sent_ids = set()
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sent_ids = set(data.get('sent_report_ids', []))
        except:
            pass
    
    initial_count = len(sent_ids)
    
    # Quét tất cả file CSV để lấy ID mới
    for name, path in sources.items():
        if not os.path.exists(path):
            continue
            
        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
            if 'title' not in df.columns:
                continue
                
            for _, row in df.iterrows():
                # Tạo ID theo logic mới: MD5 của title
                title = str(row['title']).strip()
                new_id = hashlib.md5(title.encode('utf-8')).hexdigest()
                sent_ids.add(new_id)
        except Exception as e:
            print(f"❌ Lỗi đọc {name}: {e}")

    # Lưu lại
    os.makedirs(os.path.dirname(SENT_FILE), exist_ok=True)
    with open(SENT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'sent_report_ids': list(sent_ids),
            'updated': pd.Timestamp.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã đồng bộ xong!")
    print(f"📊 Số lượng ID trong lịch sử: {initial_count} -> {len(sent_ids)}")
    print(f"🚀 Từ giờ bot sẽ chỉ gửi tin mới thực sự.")

if __name__ == "__main__":
    sync_sent_reports()
