🎯 Mục tiêu

Tài liệu này mô tả chi tiết để AI Agent có thể tự động sinh ra Payment Service và Shipping Service sử dụng Django (RESTful API).

🧩 1. Payment Service
1.1 Công nghệ yêu cầu
Framework: Django + Django REST Framework
Database: PostgreSQL hoặc MySQL
Kiến trúc: REST API
1.2 Model

Tạo model Payment với cấu trúc sau:

class Payment(models.Model):
    order_id = models.IntegerField()
    amount = models.FloatField()
    status = models.CharField(max_length=50)
1.3 Trạng thái

Define các trạng thái cố định:

PAYMENT_STATUS = [
    ("Pending", "Pending"),
    ("Success", "Success"),
    ("Failed", "Failed"),
]
Mặc định khi tạo payment: Pending
1.4 API Endpoints
1.4.1 Thanh toán đơn hàng

Endpoint:

POST /payment/pay

Request Body:

{
  "order_id": 1,
  "amount": 100.5
}

Logic:

Tạo bản ghi Payment mới
Set status = "Pending"
Giả lập xử lý thanh toán:
Thành công → "Success"
Thất bại → "Failed"

Response:

{
  "order_id": 1,
  "status": "Success"
}
1.4.2 Kiểm tra trạng thái thanh toán

Endpoint:

GET /payment/status?order_id=1

Response:

{
  "order_id": 1,
  "status": "Success"
}
1.5 Yêu cầu xử lý
Validate dữ liệu đầu vào
Nếu không tìm thấy payment → trả về lỗi 404
Logging cơ bản cho mỗi request
🚚 2. Shipping Service
2.1 Công nghệ yêu cầu
Framework: Django + Django REST Framework
Database: PostgreSQL hoặc MySQL
2.2 Model

Tạo model Shipment:

class Shipment(models.Model):
    order_id = models.IntegerField()
    address = models.TextField()
    status = models.CharField(max_length=50)
2.3 Trạng thái
SHIPPING_STATUS = [
    ("Processing", "Processing"),
    ("Shipping", "Shipping"),
    ("Delivered", "Delivered"),
]
Mặc định: Processing
2.4 API Endpoints
2.4.1 Tạo đơn vận chuyển

Endpoint:

POST /shipping/create

Request Body:

{
  "order_id": 1,
  "address": "Hà Nội, Việt Nam"
}

Logic:

Tạo Shipment mới
status = "Processing"

Response:

{
  "order_id": 1,
  "status": "Processing"
}
2.4.2 Kiểm tra trạng thái vận chuyển

Endpoint:

GET /shipping/status?order_id=1

Response:

{
  "order_id": 1,
  "status": "Shipping"
}
2.5 Logic chuyển trạng thái (gợi ý cho AI)
Processing → Shipping
Shipping → Delivered

(Có thể implement bằng cron job hoặc API update sau)

🔗 3. Integration Flow

Luồng hoạt động chuẩn:

Order Service tạo đơn hàng
Gọi Payment Service /payment/pay
Nếu thanh toán Success:
Gọi Shipping Service /shipping/create
Theo dõi:
/payment/status
/shipping/status
⚙️ 4. Yêu cầu chung cho AI Agent

AI Agent cần:

Tạo đầy đủ:
models.py
serializers.py
views.py
urls.py
Sử dụng Django REST Framework (APIView hoặc ViewSet)
Mapping URL đúng theo API đã mô tả
Trả response JSON chuẩn
Có xử lý lỗi:
400: Bad Request
404: Not Found
Code rõ ràng, tách layer hợp lý
✅ 5. Output mong muốn

Sau khi generate, hệ thống phải có:

Payment Service chạy độc lập (port riêng)
Shipping Service chạy độc lập (port riêng)
Có thể test bằng Postman:
Thanh toán
Tạo shipment
Check status