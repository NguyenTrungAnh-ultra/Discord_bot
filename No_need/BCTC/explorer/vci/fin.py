import requests
import pandas as pd
import json
from typing import Optional, Literal
from core.utils.user_agent import get_headers
from core.utils.logger import get_logger

logger = get_logger(__name__)

class VCIFinancial:
    """
    Module chuyên biệt để lấy báo cáo tài chính chi tiết từ nguồn Vietcap (VCI).
    Dữ liệu giữ nguyên bản, đầy đủ các khoản mục kế toán, không tính toán chỉ số phụ.
    """

    def __init__(self, symbol: str, random_agent: bool = False):
        self.symbol = symbol.upper()
        # Sử dụng header giả lập để tránh bị chặn
        self.headers = get_headers(data_source='VCI', random_agent=random_agent)
        self.base_url = "https://trading.vietcap.com.vn/api/stock"

    def _fetch_and_process(self, report_type: int, period: int, lang: str = 'vi') -> pd.DataFrame:
        """
        Hàm nội bộ để gọi API và xử lý dữ liệu thô.
        
        Tham số:
            - report_type: 1 (Cân đối kế toán), 2 (Kết quả kinh doanh), 3 (Lưu chuyển tiền tệ)
            - period: 1 (Năm), 2 (Quý)
        """
        url = f"{self.base_url}/{self.symbol}/financial-statements"
        
        # Payload chuẩn của VCI
        params = {
            "type": report_type,
            "period": period,
            "lang": lang
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"Không có dữ liệu {self.symbol} cho loại báo cáo này.")
                return pd.DataFrame()

            # --- Giai đoạn 1: Phẳng hóa dữ liệu (Flattening) ---
            # Dữ liệu VCI trả về dạng danh sách các kỳ, trong mỗi kỳ có danh sách các khoản mục.
            # Chúng ta cần 'bóc' nó ra thành dạng bảng dọc trước.
            
            records = []
            for period_data in data:
                # Xác định nhãn thời gian (Time Label)
                year = period_data.get('year')
                quarter = period_data.get('quarter')
                
                if period == 2: # Quý
                    time_label = f"{year}-Q{quarter}"
                else: # Năm
                    time_label = f"{year}"

                # Duyệt qua từng khoản mục trong kỳ báo cáo đó
                for item in period_data.get('values', []):
                    row = {
                        'time': time_label,
                        'id': item.get('id'), # Mã khoản mục (VD: 10100)
                        'parent_id': item.get('parentId'), # Mã cha (để dựng cây nếu cần)
                        'item_code': item.get('code'), # Mã code text (VD: 'ASSETS')
                        'item_name': item.get('name'), # Tên hiển thị (VD: 'TỔNG TÀI SẢN')
                        'value': item.get('value') # Giá trị
                    }
                    records.append(row)

            if not records:
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # --- Giai đoạn 2: Xoay bảng (Pivoting) ---
            # Chuyển đổi để:
            # - Index (Hàng): Mã khoản mục, Tên khoản mục
            # - Columns (Cột): Các mốc thời gian (Quý/Năm)
            # - Values: Giá trị tài chính
            
            # Sắp xếp để đảm bảo cột thời gian hiển thị đúng thứ tự
            df.sort_values(by=['id', 'time'], inplace=True)
            
            pivot_df = df.pivot_table(
                index=['id', 'item_name', 'item_code'], 
                columns='time', 
                values='value',
                aggfunc='first' # Đảm bảo lấy giá trị duy nhất
            )

            # Đưa cột thời gian mới nhất về bên trái (tùy chọn, thường dễ nhìn hơn)
            pivot_df = pivot_df[sorted(pivot_df.columns, reverse=True)]
            
            # Reset index để biến index thành cột bình thường, dễ thao tác sau này
            pivot_df.reset_index(inplace=True)
            
            # Đổi tên cột cho chuẩn
            pivot_df.rename(columns={
                'id': 'account_id',
                'item_name': 'account_name',
                'item_code': 'account_code'
            }, inplace=True)

            return pivot_df

        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu từ VCI: {str(e)}")
            return pd.DataFrame()

    def balance_sheet(self, period: Literal['year', 'quarter'] = 'quarter') -> pd.DataFrame:
        """
        Lấy Bảng Cân Đối Kế Toán (Balance Sheet).
        
        Tham số:
            - period: 'year' (Năm) hoặc 'quarter' (Quý)
        """
        period_id = 1 if period == 'year' else 2
        return self._fetch_and_process(report_type=1, period=period_id)

    def income_statement(self, period: Literal['year', 'quarter'] = 'quarter') -> pd.DataFrame:
        """
        Lấy Báo Cáo Kết Quả Kinh Doanh (Income Statement).
        
        Tham số:
            - period: 'year' (Năm) hoặc 'quarter' (Quý)
        """
        period_id = 1 if period == 'year' else 2
        return self._fetch_and_process(report_type=2, period=period_id)

    def cash_flow(self, period: Literal['year', 'quarter'] = 'quarter') -> pd.DataFrame:
        """
        Lấy Báo Cáo Lưu Chuyển Tiền Tệ (Cash Flow).
        
        Tham số:
            - period: 'year' (Năm) hoặc 'quarter' (Quý)
        """
        period_id = 1 if period == 'year' else 2
        return self._fetch_and_process(report_type=3, period=period_id)


if __name__ == "__main__":
    vci = VCIFinancial("HPG")
    
    # Lấy cân đối kế toán theo quý
    bs = vci.balance_sheet(period='quarter')
    print("Balance Sheet:")
    print(bs.head())

    # Lấy kết quả kinh doanh theo năm
    inc = vci.income_statement(period='year')
    print("\nIncome Statement:")
    print(inc.head())