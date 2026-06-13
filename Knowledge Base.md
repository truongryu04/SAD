# KNOWLEDGE BASE - Kien truc va Ke hoach Phat trien

## 1) Muc tieu

Xay dung mot Knowledge Base trung tam cho he sinh thai e-commerce microservices, de phuc vu:

- Recommendation (goi y san pham theo hanh vi va quan he)
- Chatbot RAG (tra loi theo du lieu he thong)
- Semantic Search (tim kiem theo y nghia)

Ket qua mong muon:

- Dong bo du lieu gan realtime tu cac service nghiep vu
- Luu tru tri thuc o 3 lop: Normalized Store + Graph DB + Vector DB
- Cung cap API truy van thong nhat cho ai-service

---

## 2) Kien truc tong the

                               Microservices
 (product, order, customer, inventory, category, attribute)
                                                                         |
                                                                         v
                                          Knowledge Collector Service
                                     (ingest + normalize + event consume)
                                                                         |
                                                                         v
------------------------------------------------------------
|                      KNOWLEDGE BASE                       |
|----------------------------------------------------------|
| 1) Normalized Data Store (PostgreSQL)                    |
| 2) Graph DB (Neo4j)                                      |
| 3) Vector DB (FAISS/Pinecone)                            |
------------------------------------------------------------
                                                                         |
                                                                         v
                                                       AI SERVICE (ai-service)
                                           - recommendation
                                           - chatbot (RAG)
                                           - semantic search
                                                                         |
                                                                         v
                                                                  API Gateway

---

## 3) Thanh phan chi tiet

### 3.1 Knowledge Collector Service

Vai tro:

- Gom data tu service nguon (API pull + event streaming)
- Chuan hoa schema ve mot model thong nhat
- Upsert vao Normalized Store
- Dong bo tiep sang Graph DB va Vector DB

Kieu dong bo:

- Initial full sync: quet du lieu goc theo lo
- Incremental sync: event-driven (CDC/event bus)
- Reconciliation job: doi soat dinh ky de sua sai lech

### 3.2 Normalized Data Store (de xuat PostgreSQL)

Vai tro:

- Nguon su that da chuan hoa
- De audit, replay, backfill, analytics
- Lam staging cho graph/vector indexing

Bang de xuat (toi thieu):

- kb_products
- kb_categories
- kb_attributes
- kb_inventory
- kb_customers
- kb_orders
- kb_order_items
- kb_user_events
- kb_sync_checkpoint
- kb_dead_letter_events

### 3.3 Graph DB (Neo4j)

Muc tieu:

- Bieu dien quan he de recommendation va reasoning

Node de xuat:

- Customer
- Product
- Category
- Brand
- Attribute
- Order

Relationship de xuat:

- CUSTOMER_VIEWED_PRODUCT
- CUSTOMER_ADDED_PRODUCT
- CUSTOMER_PURCHASED_PRODUCT
- PRODUCT_IN_CATEGORY
- PRODUCT_HAS_ATTRIBUTE
- PRODUCT_SIMILAR_PRODUCT
- CUSTOMER_HAS_ORDER

Chi so/truy van:

- Constraint unique theo id business
- Index cho customer_id, product_id, category_id

### 3.4 Vector DB (FAISS hoac Pinecone)

Muc tieu:

- Tim kiem semantic cho chatbot va search

Entity duoc embedding:

- Product profile (ten, mo ta, category, attribute, brand)
- Category profile
- Knowledge snippets cho RAG

Metadata bat buoc:

- entity_type
- entity_id
- source_service
- updated_at
- language

Chien luoc cap nhat vector:

- Re-embed theo event thay doi noi dung
- Rebuild batch theo lich (dem)

---

## 4) Data contract va chuan hoa

Nguyen tac:

- Moi ban ghi phai co business id on dinh
- Time zone ISO-8601 UTC
- Co version schema cho payload event

JSON event mau (rut gon):

{
      "event_id": "uuid",
      "event_type": "product.updated",
      "event_version": 1,
      "occurred_at": "2026-04-13T10:00:00Z",
      "source": "product-service",
      "payload": {
            "product_id": 101,
            "name": "Laptop ABC",
            "category_id": 2,
            "brand": "BrandX",
            "base_price": 21990000,
            "status": "ACTIVE"
      }
}

Idempotency:

- Dung event_id + checksum payload de tranh xu ly trung lap

---

## 5) Luong xu ly theo use case

### 5.1 Recommendation

Input:

- customer_id
- user_events gan day
- graph neighborhood

Pipeline de xuat:

1. Lay candidate bang graph traversal (dong hanh vi)
2. Re-rank bang score lai (view/add/purchase recency + stock + price band)
3. Loc business rule (status, ton kho)
4. Tra top-N + ly do

Output mau:

- product_id
- score
- reason_code (similar_users, viewed_related, bought_together)

### 5.2 Chatbot RAG

Pipeline de xuat:

1. Parse cau hoi va detect intent
2. Vector retrieve top-k
3. Graph expansion neu can (san pham lien quan, category lien quan)
4. Compose context + guardrail
5. Sinh cau tra loi va citation

### 5.3 Semantic search

Pipeline de xuat:

1. Embed query
2. ANN search tren Vector DB
3. Hybrid re-rank (semantic + metadata filter)
4. Tra ket qua + score

---

## 6) Dong bo realtime bang event

Cong nghe de xuat:

- Option A: Kafka
- Option B: RabbitMQ

Topic/queue de xuat:

- product.events
- category.events
- inventory.events
- customer.events
- order.events
- user_activity.events

Consumer strategy:

- At-least-once + idempotent write
- DLQ cho event loi
- Retry theo exponential backoff

---

## 7) API cho ai-service truy van KB

Nhom API noi bo de xuat:

- POST /kb/recommendations/query
- POST /kb/rag/retrieve
- POST /kb/search/semantic
- GET  /kb/health
- GET  /kb/sync/status

Response can co:

- data
- trace_id
- source_breakdown (graph/vector/store)
- latency_ms

---

## 8) Bao mat va quan tri

Bao mat:

- Service-to-service auth (JWT hoac mTLS)
- Row-level policy cho du lieu nhay cam customer
- Masking PII trong log

Quan tri du lieu:

- Data retention policy
- Versioned schema migration
- PII deletion workflow (right to be forgotten)

---

## 9) Observability

Can theo doi:

- Event lag
- Sync throughput
- Error rate theo service nguon
- Recall@k cho retrieve
- Recommendation CTR/Conversion

Dashboard de xuat:

- Sync dashboard
- KB query dashboard
- AI quality dashboard

---

## 10) Lo trinh phat trien

### Phase 1 - Foundation

- Dung Normalized Store
- Tao collector pull API theo batch
- Sync products/categories/inventory

Deliverable:

- Endpoint /kb/search/semantic ban dau

### Phase 2 - Graph + Recommendation

- Dung Neo4j + relation core
- Build recommendation query + re-rank

Deliverable:

- Endpoint /kb/recommendations/query

### Phase 3 - RAG Production

- Hybrid retrieve (vector + graph)
- Citation + guardrails

Deliverable:

- Endpoint /kb/rag/retrieve

### Phase 4 - Realtime va Van hanh

- Event bus + incremental sync
- DLQ + retry + monitoring

Deliverable:

- /kb/sync/status + dashboard van hanh

---

## 11) Mapping voi he thong hien tai

Du an hien co:

- api-gateway
- ai-service
- product-service
- customer-service
- order-service
- staff-service

Huong tich hop thuc te:

1. Dat Knowledge Collector thanh service moi (kb-collector)
2. Dat KB Query API thanh service moi (kb-query) hoac module trong ai-service
3. ai-service goi kb-query thay vi goi truc tiep tung service
4. Gateway giu nguyen contract ben ngoai

---

## 12) Definition of Done

Mot KB duoc xem la san sang khi:

- Sync day du product/category/inventory/customer/order
- Co checkpoint va recover duoc sau loi
- Recommendation API on dinh va co metric
- RAG retrieve tra citation dung
- Co monitoring + alert cho event lag va loi dong bo

---

## 13) Checklist trien khai nhanh

- [ ] Tao service kb-collector
- [ ] Tao schema normalized trong PostgreSQL
- [ ] Tich hop Neo4j writer
- [ ] Tich hop Vector writer (FAISS/Pinecone)
- [ ] Tao API kb-query cho ai-service
- [ ] Bat event sync incremental
- [ ] Bo sung metrics + dashboard
- [ ] Chay thu E2E recommendation/chatbot/search




1. Tạo và đồng bộ Knowledge Base (KB)
a. Dữ liệu nguồn

Sản phẩm, danh mục, thuộc tính, tồn kho, khách hàng, đơn hàng được lấy từ các service: product-service, customer-service, order-service.
b. Quá trình đồng bộ

Service kb-service có file collector.py với hàm run_phase1_collection().
Khi gọi endpoint /api/kb/collect/ (hoặc chạy định kỳ), collector sẽ:
Gọi API các service nguồn để lấy danh sách sản phẩm, danh mục, tồn kho, khách hàng, đơn hàng.
Lưu dữ liệu này vào bảng KBProduct, KBCategory, KBInventory, v.v. trong database của kb-service.
Đồng thời, mỗi bản ghi sẽ được ghi vào Neo4j (graph database) thông qua các hàm sync_product, sync_category, sync_customer, sync_order trong graph_writer.py.
c. Cách gọi đồng bộ

Có thể gọi POST /api/kb/collect/ (qua gateway hoặc trực tiếp vào kb-service) để trigger đồng bộ lại toàn bộ KB và graph.

2. Tạo và cập nhật graph hành vi
a. Graph lưu ở đâu?

Graph được lưu trong Neo4j (container neo4j trong docker-compose, mặc định user neo4j/12345678).
b. Dữ liệu nào được ghi vào graph?

Các node: Customer, Product, Category, SearchTerm.
Các cạnh (relationship):
Customer-[:VIEWED|ADDED_TO_CART|PURCHASED]->Product
Customer-[:SEARCHED]->SearchTerm
Product-[:PRODUCT_IN_CATEGORY]->Category
c. Cách cập nhật graph hành vi

Khi user thực hiện các hành động (xem sản phẩm, thêm vào giỏ, mua hàng, tìm kiếm), customer-service sẽ:
Ghi log vào bảng UserActivity.
Đồng thời phát sự kiện (fire-and-forget) tới endpoint /api/kb/behavior/ của kb-service (hàm _emit_kb_behavior_event trong views.py).
kb-service nhận event này ở KBBehaviorEventView, gọi sync_user_behavior trong graph_writer.py để ghi vào Neo4j.
d. Đơn hàng cũng được sync vào graph

Khi đồng bộ đơn hàng (order), collector sẽ gọi sync_order để tạo cạnh PURCHASED giữa Customer và Product.
3. Vận hành và truy vấn graph
a. Các truy vấn graph

Các truy vấn Cypher (Neo4j) được dùng để:
Lấy sản phẩm cùng danh mục, cùng được mua, cùng được xem, v.v.
Tính điểm gợi ý dựa trên hành vi đồng mua, đồng xem, cá nhân hóa, v.v.
Ví dụ: MATCH (c:Customer)-[r:VIEWED|ADDED_TO_CART|SEARCHED]->(x) RETURN p LIMIT 300;
b. API gợi ý sử dụng graph

kb-service cung cấp các endpoint như:
/api/kb/recommend/?mode=same_category
/api/kb/recommend/?mode=also_bought
/api/kb/recommend/?mode=personalized
/api/kb/recommend/top/
Các API này thực hiện truy vấn graph trong Neo4j để trả về danh sách sản phẩm gợi ý.
c. Tích hợp với AI service

AI service gọi các API trên của kb-service để lấy gợi ý graph, sau đó có thể trộn với heuristic hoặc trả về trực tiếp (mode=graph).
4. Tóm tắt luồng tạo và vận hành KB/graph
Dữ liệu gốc được lấy từ các service nguồn qua collector.
Collector ghi dữ liệu vào cả DB của kb-service và Neo4j.
Hành vi realtime (xem, mua, tìm kiếm) được ghi vào graph qua event từ customer-service.
Các API gợi ý truy vấn graph trong Neo4j để trả về kết quả.
AI service và các service khác có thể gọi các API này để lấy gợi ý sản phẩm