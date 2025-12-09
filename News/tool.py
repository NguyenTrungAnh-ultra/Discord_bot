import os 
import json

def load_history(direct:str)->list:
    """Đọc file json lấy danh sách tin đã gửi"""
    if not os.path.exists(direct):
        return []
    try:
        with open(direct, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Lỗi đọc file history: {e}")
        return []

def save_history(_list:list, direct:str, 
                 MAX_SIZE:int = 50_000
                 ):
    """Lưu danh sách vào file json"""
    try:
        trimmed_list = _list[:MAX_SIZE]
        # Save
        with open(direct, 'w', encoding='utf-8') as f:
            json.dump(trimmed_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu file history: {e}")

def update_history(_list:list, 
                   direct:str
                   ):
    # 1. Load dữ liệu cũ
    existing_data = []
    if os.path.exists(direct):
        try:
            with open(direct, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []

    # 2. Tạo tập hợp các ID đã tồn tại để kiểm tra cho nhanh (O(1))
    # Giả sử key định danh là 'id', nếu không có 'id' thì đổi thành 'news_title'
    existing_ids = {item.get('id') for item in existing_data}

    count_added = 0
    
    # 3. Duyệt danh sách mới, chỉ thêm cái nào chưa có ID trong file cũ
    for item in _list:
        item_id = item.get('id')
        
        # Chỉ thêm nếu có ID và ID đó chưa từng xuất hiện
        if item_id and item_id not in existing_ids:
            existing_data.append(item)
            existing_ids.add(item_id) # Cập nhật luôn vào set để tránh trùng lặp nội bộ
            count_added += 1

    # 4. Lưu lại toàn bộ (Cũ + Mới thêm) vào file
    if count_added > 0:
        with open(direct, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        print(f"Đã lưu thêm {count_added} tin mới vào {direct}.")
    else:
        print("Không có tin mới cần lưu (tất cả đã tồn tại trong file).")
