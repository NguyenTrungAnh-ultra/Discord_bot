# 1. Dùng image chính chủ của Playwright (đã có sẵn Python và Trình duyệt)
# Chọn phiên bản khớp với phiên bản playwright trong requirements.txt của bạn
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

# 2. Tạo thư mục làm việc
WORKDIR /app

# 3. Copy file requirements và cài thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy code của bạn vào
COPY . .

# Đảm bảo log luôn được in ra ngay lập tức (không bị lưu đệm)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 6. Chạy bot
CMD ["python", "main.py"]
