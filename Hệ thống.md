# Knowledge Base - SA-AD_EMCOMERCE_AI

## 1) Tong quan he thong

Du an la mo hinh e-commerce theo kien truc microservices, trien khai qua Docker Compose, gom cac nhom chuc nang:

- API Gateway (UI + reverse proxy)
- Nhom Customer/Cart/Order
- Nhom Product/Category/Attribute/Inventory
- Nhom AI (goi y san pham + chat)
- Nhom Staff (quan tri san pham/don hang/khach hang)

Muc tieu cua he thong:

- Tach nghiep vu theo service de de scale va bao tri.
- Dong bo du lieu voi seed script cho moi lan khoi dong moi truong local.
- Cung cap giao dien Customer va Staff thong nhat qua Gateway.

---

## 2) Kien truc tong the

### 2.1 Thanh phan chinh

- `api-gateway`: diem vao duy nhat cho UI va API proxy.
- `customer-service`: account, cart, cart items, rating, search history, user activity.
- `order-service`: checkout va quan ly don.
- `product-service`: quan ly toan bo product domain (product, category, attribute, inventory).
- `staff-service`: API cho trang quan tri.
- `ai-service`: recommendation va chatbot.

### 2.2 Co so du lieu

- MySQL:
	- customer_service_db
	- order_service_db
	- staff_service_db
- PostgreSQL:
	- product_service_db
	- ai_service_db

---

## 3) Vai tro API Gateway

Gateway dam nhiem 2 vai tro:

1. Phuc vu trang UI (`/ui/...`) cho Customer/Staff.
2. Proxy request toi service dich, gom:
	 - `/api/products/`
	 - `/api/categories/`
	 - `/api/customer/...`
	 - `/api/orders/...`
	 - `/api/ai/...`
	 - `/api/staff/...`

Co che dang nhap session tai Gateway:

- Luu role (`CUSTOMER`/`STAFF`), username, full_name, user_id trong session.
- Route UI co check role truoc khi render.

---

## 4) Luong nghiep vu chinh

### 4.1 Customer browsing + cart + checkout

1. Customer login qua Gateway.
2. UI lay products/categories tu Gateway proxy.
3. Them san pham vao cart qua `/api/customer/cart-items/`.
4. Checkout qua `/api/orders/checkout/`.
5. Trang cart cap nhat so luong/xoa item qua API cart item detail.

### 4.2 AI recommendation

1. UI goi `/api/ai/recommendations/<customer_id>/`.
2. Gateway proxy sang ai-service.
3. ai-service tinh diem tu activity + xu huong tong.
4. Neu AI service loi ket noi, UI fallback sang local recommendation (lay tu danh sach san pham hien co).

### 4.3 Staff operations

1. Staff login qua Gateway.
2. Quan ly danh sach item/category/order/customer tu cac endpoint staff/category/order/customer.
3. Staff service co fallback product-source de tranh trang thai danh sach rong khi service cu khong con du lieu.

---

## 5) UI/UX hien tai (tom tat)

### 5.1 Customer

- Header da chuyen sang icon-based account/cart.
- Account menu gom:
	- Thay doi thong tin ca nhan
	- Logout
- Trang products ho tro:
	- Filter: price, brand, rating, color, size
	- Sort: price asc/desc, best selling, newest
	- Badge `AI pick` tren card duoc de xuat

### 5.2 Staff

- Dashboard + pages cho Products, Categories, Orders, Customers.
- Shared CSS/JS de dong bo giao dien va hanh vi.

---

## 6) Du lieu mau (seed)

Du an da co co che seed tu dong khi `docker compose up`:

- `mysql-seeder`
- `postgres-seeder`

Du lieu seed gom:

- Danh muc san pham thuc te (10 category)
- San pham map dung category
- Gia tien phu hop tung nhom san pham

Muc tieu seed:

- Moi truong local co du lieu ngay.
- Giam cong setup thu cong.
- Dam bao test UI/flow co du lieu thuc te.

---

## 7) Van de da gap va cach xu ly

### 7.1 Trang customer khong hien thi san pham

Nguyen nhan:

- Frontend ky vong payload dang `{ data: [...] }`.
- API thuc te tra ve mang truc tiep `[...]`.

Xu ly:

- Chuan hoa parser de chap nhan ca 2 dang.

### 7.2 AI recommendation loi ket noi

Nguyen nhan:

- ai-service khong san sang/connection refused.

Xu ly:

- UI fallback local recommendation.
- Van hien thi du lieu + badge AI pick de khong vo UX.

### 7.3 Header customer lech bo cuc

Xu ly:

- Can lai header theo khung bao ngoai.
- Tinh chinh nhom trai-phai cho icon/menu.

---

## 8) Runbook van hanh nhanh

### 8.1 Build va chay

- `docker compose up -d --build`

### 8.2 Rebuild rieng Gateway sau khi sua template/CSS/JS

- `docker compose up -d --build api-gateway`

### 8.3 Kiem tra endpoint nhanh

- Products: `http://localhost:8000/api/products/`
- Categories: `http://localhost:8000/api/categories/`
- Customer UI: `http://localhost:8000/ui/customer/`
- Staff UI: `http://localhost:8000/ui/staff/`

---

## 9) Dinh huong cai tien tiep theo

- Dong nhat response contract giua cac service (tranh parser 2 kieu).
- Them healthcheck chi tiet cho ai-service va dependency retry.
- Bo sung observability: request id, tracing, dashboard log.
- Them test E2E cho 3 flow: login -> browse -> checkout.
- Nang cap profile edit thanh modal thay vi prompt.

---

## 10) Glossary ngan

- Gateway: service trung gian cho UI va API routing.
- Fallback: hanh vi du phong khi service chinh loi.
- Seed data: du lieu khoi tao de test/chay local.
- AI pick: nhan danh dau san pham duoc AI de xuat.

