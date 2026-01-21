"""
PDF Download functionality for VCBS reports
"""

import os
import requests
from typing import Dict, Optional
import pandas as pd


def download_pdf(report_info: Dict, output_dir: Optional[str] = None) -> Dict:
    """
    Download PDF for a specific report
    
    Args:
        report_info: Dictionary with report information (must have pdf_url or download_url)
        output_dir: Optional custom output directory
        
    Returns:
        Dictionary with download results
    """
    # Get PDF URL
    pdf_url = report_info.get('pdf_url') or report_info.get('download_url')
    
    if not pdf_url:
        return {
            'success': False,
            'error': 'No PDF URL available',
            'report_id': report_info.get('report_id', '')
        }
    
    # Determine output directory
    if output_dir is None:
        base_dir = r".\temp\reports\VCBS"
        report_type = report_info.get('report_type', 'BCDN')
        
        # Map report type to directory
        type_dirs = {
            'BCVM': 'bao_cao_vi_mo',
            'BCDN': 'bao_cao_doanh_nghiep',
            'BCN': 'bao_cao_nganh',
            'BCPS': 'bao_cao_chung_khoan_phai_sinh',
            'BCTT': 'bao_cao_thi_truong',
            'BCTP': 'bao_cao_trai_phieu'
        }
        
        type_dir = type_dirs.get(report_type, 'other')
        output_dir = os.path.join(base_dir, type_dir)
        
        # Add subdirectory for ticker/industry if available
        if report_info.get('ticker'):
            output_dir = os.path.join(output_dir, report_info['ticker'])
        elif report_info.get('industry'):
            output_dir = os.path.join(output_dir, report_info['industry'])
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename from title
    title = report_info.get('title', 'report')
    # Clean filename
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = filename[:100]  # Limit length
    filename = f"{filename}.pdf"
    
    output_path = os.path.join(output_dir, filename)
    
    # Check if already downloaded
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024  # KB
        return {
            'success': True,
            'already_exists': True,
            'file_path': output_path,
            'file_size_kb': file_size,
            'report_id': report_info.get('report_id', '')
        }
    
    try:
        # Download PDF
        print(f"📥 Downloading: {title}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.vcbs.com.vn/'
        }
        
        response = requests.get(pdf_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save PDF
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024  # KB
        print(f"   ✅ Downloaded: {filename} ({file_size:.1f} KB)")
        
        return {
            'success': True,
            'already_exists': False,
            'file_path': output_path,
            'file_size_kb': file_size,
            'report_id': report_info.get('report_id', '')
        }
        
    except Exception as e:
        print(f"   ❌ Error downloading: {e}")
        return {
            'success': False,
            'error': str(e),
            'report_id': report_info.get('report_id', '')
        }


def download_reports_from_csv(csv_path: str, max_downloads: Optional[int] = None) -> Dict:
    """
    Download PDFs for all reports in CSV that haven't been downloaded yet
    
    Args:
        csv_path: Path to CSV file containing report information
        max_downloads: Optional limit on number of downloads
        
    Returns:
        Dictionary with download statistics
    """
    if not os.path.exists(csv_path):
        return {
            'success': False,
            'error': f'CSV file not found: {csv_path}'
        }
    
    # Load CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Filter undownloaded reports with PDF URLs
    to_download = df[
        (df['downloaded'] == False) & 
        ((df['pdf_url'].notna() & (df['pdf_url'] != '')) | 
         (df['download_url'].notna() & (df['download_url'] != '')))
    ]
    
    if max_downloads:
        to_download = to_download.head(max_downloads)
    
    total = len(to_download)
    print(f"\n📊 Found {total} reports to download\n")
    
    if total == 0:
        return {
            'success': True,
            'total_reports': total,
            'downloaded': 0,
            'already_existed': 0,
            'failed': 0
        }
    
    downloaded = 0
    already_existed = 0
    failed = 0
    
    for idx, row in to_download.iterrows():
        report_dict = row.to_dict()
        result = download_pdf(report_dict)
        
        if result['success']:
            if result.get('already_exists'):
                already_existed += 1
            else:
                downloaded += 1
            
            # Update CSV
            df.at[idx, 'downloaded'] = True
            df.at[idx, 'download_path'] = result['file_path']
        else:
            failed += 1
    
    # Save updated CSV
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 Updated CSV: {csv_path}")
    
    return {
        'success': True,
        'total_reports': total,
        'downloaded': downloaded,
        'already_existed': already_existed,
        'failed': failed
    }


if __name__ == "__main__":
    # Test downloading from CSV
    csv_path = r".\temp\reports\VCBS\bao_cao_doanh_nghiệp\vcbs_reports.csv"
    
    if os.path.exists(csv_path):
        result = download_reports_from_csv(csv_path, max_downloads=5)
        
        print(f"\n{'='*60}")
        print("📊 Download Results:")
        print(f"  Total: {result['total_reports']}")
        print(f"  Downloaded: {result['downloaded']}")
        print(f"  Already existed: {result['already_existed']}")
        print(f"  Failed: {result['failed']}")
        print(f"{'='*60}")
    else:
        print(f"❌ CSV not found: {csv_path}")
