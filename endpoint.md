Tổng quan node và quan hệ
MATCH (n) RETURN n LIMIT 300;

Chỉ xem các quan hệ PURCHASED
MATCH p=(:Customer)-[:PURCHASED]->(:Product)
RETURN p
LIMIT 300;

Xem các customer mua cùng sản phẩm (co-purchase)
MATCH p=(c1:Customer)-[:PURCHASED]->(pr:Product)<-[:PURCHASED]-(c2:Customer)
WHERE c1.id < c2.id
RETURN p
LIMIT 200;

Xem trọng số và thời gian của PURCHASED
MATCH (c:Customer)-[r:PURCHASED]->(p:Product)
RETURN c.id AS customer_id, p.id AS product_id, r.weight AS weight, r.rating AS rating, r.timestamp AS ts
ORDER BY ts DESC
LIMIT 100;

Xem graph theo một customer cụ thể
MATCH p=(c:Customer {id: 1})-[r]->(n)
RETURN p
LIMIT 200;

Xem graph theo một product cụ thể
MATCH p=(c:Customer)-[r]->(pr:Product {id: 6})
RETURN p
LIMIT 200;

Customer -> Purchased -> Product -> Category
MATCH p=(c:Customer)-[:PURCHASED]->(pr:Product)-[:IN_CATEGORY]->(cat:Category)
RETURN p
LIMIT 250;

Top sản phẩm được mua nhiều nhất
MATCH (:Customer)-[r:PURCHASED]->(p:Product)
RETURN p.id AS product_id, p.name AS product_name, count(r) AS purchases
ORDER BY purchases DESC
LIMIT 20;

Top customer hoạt động mua nhiều nhất
MATCH (c:Customer)-[r:PURCHASED]->(:Product)
RETURN c.id AS customer_id, count(r) AS purchase_edges
ORDER BY purchase_edges DESC
LIMIT 20;

Phân bố mua theo category
MATCH (:Customer)-[:PURCHASED]->(p:Product)-[:IN_CATEGORY]->(cat:Category)
RETURN cat.id AS category_id, cat.name AS category_name, count(*) AS purchase_count
ORDER BY purchase_count DESC
LIMIT 20;

Nếu có hành vi VIEWED/ADDED_TO_CART/SEARCHED thì xem nhanh
MATCH p=(c:Customer)-[r:VIEWED|ADDED_TO_CART|SEARCHED]->(x)
RETURN p
LIMIT 300;

Kiểm tra số lượng từng loại quan hệ
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(*) AS cnt
ORDER BY cnt DESC;













Dưới đây là gợi ý API endpoint mẫu cho từng service mới (chuẩn RESTful, tiền tố /api/):

Product Service

GET /api/products/ — Danh sách sản phẩm
POST /api/products/ — Thêm sản phẩm mới
GET /api/products/{id}/ — Chi tiết sản phẩm
PUT /api/products/{id}/ — Cập nhật sản phẩm
DELETE /api/products/{id}/ — Xóa sản phẩm
GET /api/products/{id}/variants/ — Danh sách biến thể sản phẩm
POST /api/products/{id}/variants/ — Thêm biến thể cho sản phẩm

Category Service

GET /api/categories/ — Danh sách danh mục
POST /api/categories/ — Thêm danh mục mới
GET /api/categories/{id}/ — Chi tiết danh mục
PUT /api/categories/{id}/ — Cập nhật danh mục
DELETE /api/categories/{id}/ — Xóa danh mục

Attribute Service

GET /api/attributes/ — Danh sách thuộc tính
POST /api/attributes/ — Thêm thuộc tính mới
GET /api/attributes/{id}/ — Chi tiết thuộc tính
PUT /api/attributes/{id}/ — Cập nhật thuộc tính
DELETE /api/attributes/{id}/ — Xóa thuộc tính
GET /api/category-attributes/ — Danh sách thuộc tính theo danh mục
POST /api/category-attributes/ — Gán thuộc tính cho danh mục
GET /api/product-attribute-values/ — Danh sách giá trị thuộc tính sản phẩm
POST /api/product-attribute-values/ — Thêm giá trị thuộc tính cho sản phẩm
Inventory Service

GET /api/inventories/ — Danh sách tồn kho
POST /api/inventories/ — Thêm tồn kho cho biến thể
GET /api/inventories/{id}/ — Chi tiết tồn kho
PUT /api/inventories/{id}/ — Cập nhật tồn kho
GET /api/stock-transactions/ — Lịch sử giao dịch kho
POST /api/stock-transactions/ — Tạo giao dịch nhập/xuất kho