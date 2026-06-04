import os
import requests
import pandas as pd
from src.utils.user_agent import get_random_desktop_user_agent

class BaseScanner:
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.output_dir = os.path.join(os.getcwd(), "temp", "reports", self.source_name)
        self.csv_file = os.path.join(self.output_dir, f"{self.source_name.lower()}_reports.csv")

    def setup(self, use_url_as_id=False):
        """Setup directories and load existing data"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        session = requests.Session()
        user_agent = get_random_desktop_user_agent()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': self.base_url
        })
        
        existing_items = set()
        old_df = pd.DataFrame()
        if os.path.exists(self.csv_file):
            try:
                old_df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
                if use_url_as_id and 'pdf_url' in old_df.columns:
                    existing_items = set(old_df['pdf_url'].tolist())
                elif 'report_id' in old_df.columns:
                    existing_items = set(old_df['report_id'].tolist())
                print(f"📂 Đã load {len(old_df)} báo cáo cũ từ file CSV")
            except Exception as e:
                print(f"⚠️ Không thể load CSV cũ, sẽ tạo mới: {e}")
        
        return session, old_df, existing_items

    def save_csv(self, final_df: pd.DataFrame):
        final_df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
        print(f"💾 Đã lưu vào file: {self.csv_file}")

    def download_by_id(self, report_id: str):
        """
        Download PDF by report ID
        """
        if not os.path.exists(self.csv_file):
            return {'success': False, 'report_id': report_id, 'title': '', 'file_path': '', 'error': 'CSV file not found.'}
        
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8-sig')
        except Exception as e:
            return {'success': False, 'report_id': report_id, 'title': '', 'file_path': '', 'error': f'Error loading CSV: {e}'}
        
        report = df[df['report_id'] == report_id]
        if report.empty:
            return {'success': False, 'report_id': report_id, 'title': '', 'file_path': '', 'error': f'Report not found with ID: {report_id}'}
        
        report_row = report.iloc[0]
        pdf_url = report_row.get('pdf_url', '')
        title = report_row.get('title', '')
        
        if not pdf_url or pd.isna(pdf_url):
            return {'success': False, 'report_id': report_id, 'title': title, 'file_path': '', 'error': 'No PDF URL for this report'}
        
        existing_path = report_row.get('download_path', '')
        if existing_path and not pd.isna(existing_path) and os.path.exists(existing_path):
            print(f"✅ File đã tồn tại: {existing_path}")
            return {'success': True, 'report_id': report_id, 'title': title, 'file_path': existing_path, 'error': ''}
        
        download_dir = os.path.join(self.output_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        filename = pdf_url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename = f"{report_id[:8]}.pdf"
        
        file_path = os.path.join(download_dir, filename)
        print(f"📥 Đang tải: {title[:50]}...")
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': get_random_desktop_user_agent(),
                'Accept': 'application/pdf,*/*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Referer': self.base_url
            })
            
            response = session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content) / 1024
            print(f"✅ Đã tải: {filename} ({file_size:.1f} KB)")
            
            df.loc[df['report_id'] == report_id, 'download_path'] = file_path
            self.save_csv(df)
            
            return {'success': True, 'report_id': report_id, 'title': title, 'file_path': file_path, 'error': ''}
            
        except Exception as e:
            print(f"❌ Lỗi tải file: {e}")
            return {'success': False, 'report_id': report_id, 'title': title, 'file_path': '', 'error': str(e)}
