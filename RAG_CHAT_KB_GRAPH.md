# Tai lieu: Xay dung RAG va Chat dua tren KB_Graph

## 1. Muc tieu

Tai lieu nay mo ta cach he thong xay dung chat va goi y san pham dua tren:
- Knowledge Base (KB) dong bo tu cac microservice
- Knowledge Graph tren Neo4j (KB_Graph)
- RAG retrieval (vector + graph)

Phien ban hien tai da bo phu thuoc mo hinh Ollama trong luong chat.
Chat duoc tao cau tra loi bang co che rule-based tren du lieu RAG + KB_Graph.

---

## 2. Pham vi

Tai lieu bao gom:
- Kien truc du lieu KB va KB_Graph
- Luong dong bo du lieu vao graph
- Luong truy van RAG cho chat
- Luong goi y san pham
- API dang dung trong he thong
- Cach van hanh va kiem thu

Tai lieu khong bao gom:
- Huong dan huan luyen model LLM
- Bai toan NLP nang cao (intent classification phuc tap)

---

## 3. Kien truc tong quan

Nguon du lieu:
- product-service
- customer-service
- order-service
- (cac service khac trong he)

Lop tri thuc:
- Normalized store (PostgreSQL)
- Graph store (Neo4j)
- Vector index (pgvector trong ai-service)

Service tieu thu:
- kb-service: quan ly dong bo va truy van graph
- ai-service: chat RAG va recommendation

So do luong:

1. Cac service nguon phat sinh du lieu
2. kb-service collect va sync vao Neo4j
3. ai-service lay du lieu tu product-service de lap chi muc vector
4. ai-service goi kb-service de lay ket qua graph
5. ai-service hop nhat vector context + graph context
6. ai-service sinh cau tra loi/chat hoac danh sach goi y

---

## 4. Mo hinh du lieu KB_Graph

### 4.1 Node chinh
- Customer
- Product
- Category
- Brand
- Attribute
- Order
- SearchTerm
- BehaviorEvent
- Day

### 4.2 Relationship chinh
- Customer-[:VIEWED]->Product
- Customer-[:ADDED_TO_CART]->Product
- Customer-[:PURCHASED]->Product
- Customer-[:SEARCHED]->SearchTerm
- Product-[:PRODUCT_IN_CATEGORY]->Category
- Product-[:PRODUCT_OF_BRAND]->Brand
- Product-[:PRODUCT_HAS_ATTRIBUTE]->Attribute
- Customer-[:PLACED_ORDER]->Order
- Order-[:ORDER_CONTAINS]->Product
- Customer-[:PERFORMED]->BehaviorEvent
- BehaviorEvent-[:ON_PRODUCT]->Product
- BehaviorEvent-[:ON_SEARCH_TERM]->SearchTerm
- BehaviorEvent-[:IN_DAY]->Day

### 4.3 Rang buoc va toan ven
- Dung CREATE CONSTRAINT ... IF NOT EXISTS cho cac id duy nhat
- Dung MERGE de upsert node/edge, dam bao idempotent

---

## 5. Thanh phan va vai tro trong code

### 5.1 kb-service
- graph_writer.py:
  - Tao ket noi Neo4j
  - Khoi tao schema/constraint
  - upsert Product, Category, Customer, Order
  - Ghi event hanh vi user vao graph
  - Truy van recommendation graph

- collector.py:
  - Goi API service nguon
  - Chuan hoa du lieu
  - Vua ghi vao DB KB vua goi ham sync_* de ghi Neo4j

- views.py:
  - Endpoint collect
  - Endpoint nhan event behavior
  - Endpoint recommendation graph

### 5.2 ai-service
- chatbot.py:
  - ProductKnowledgeBase: nap du lieu san pham
  - VectorStoreService: embedding va retrieve top-k
  - EcomRAGChatbot:
    - retrieve vector context
    - retrieve graph context qua KBGraphRecommender
    - merge context
    - tao cau tra loi rule-based (khong dung Ollama)

- recommender.py:
  - KBGraphRecommender goi endpoint graph tu kb-service
  - ProductRecommenderService hop nhat score activity + graph + lstm (neu bat)

- views.py:
  - /ai/chat/ cho chat thuong (vector_only)
  - /ai/chat/graph-rag/ cho chat RAG co graph mode
  - /ai/recommendations/{customer_id}/ cho recommendation

---

## 6. Co che RAG trong chat

### 6.1 Dau vao
- question
- customer_id (tuy chon)
- product_id (tuy chon)
- top_k
- rag_mode
- bo loc: price_range, gender

### 6.2 Cac che do rag_mode
- vector_only: chi dung vector retrieval
- graph_only: chi dung graph retrieval
- graph_hybrid: ket hop vector + graph
- personalized: uu tien graph theo customer_id
- product: uu tien graph theo product_id

### 6.3 Pipeline chat
1. Nap danh muc san pham tu product-service
2. Upsert vao vector index
3. Retrieve vector theo question (neu mode cho phep)
4. Retrieve graph tu kb-service
5. Merge, deduplicate context
6. Sap xep theo logic cau hoi (vd: re nhat/dat nhat)
7. Sinh cau tra loi rule-based tu danh sach context
8. Tra ve answer + sources + thong ke context

### 6.4 Dinh dang ket qua chat
- message
- request_id
- model: "rag-kb"
- answer
- sources
- context_count
- vector_context_count
- graph_context_count
- rag_mode

---

## 7. Co che recommendation dua tren KB_Graph

### 7.1 Muc tieu
Dung graph de tim san pham lien quan theo:
- cung category
- dong mua (also bought)
- ca nhan hoa theo hanh vi
- top product fallback

### 7.2 API recommendation trong ai-service
- GET /ai/recommendations/{customer_id}/?mode=activity|graph|hybrid|lstm|hybrid_lstm&limit=...

### 7.3 API recommendation trong kb-service
- GET /api/kb/recommend/?mode=same_category&product_id=...&limit=...
- GET /api/kb/recommend/?mode=also_bought&product_id=...&limit=...
- GET /api/kb/recommend/?mode=personalized&customer_id=...&limit=...
- GET /api/kb/recommend/top/?limit=...

---

## 8. API chat dang su dung

### 8.1 Chat thuong (vector)
- POST /ai/chat/

Body mau:
{
  "question": "goi y laptop tam trung cho hoc tap",
  "top_k": 5
}

### 8.2 Chat Graph-RAG
- POST /ai/chat/graph-rag/

Body mau:
{
  "question": "goi y theo hanh vi mua cua toi",
  "customer_id": 1,
  "top_k": 5,
  "rag_mode": "graph_hybrid",
  "price_range": "mid",
  "gender": "unisex"
}

---

## 9. Van hanh he thong

### 9.1 Khoi dong
- docker compose up -d --build

### 9.2 Dong bo KB + Graph
- POST /api/kb/collect/

### 9.3 Kiem tra suc khoe
- GET /health/ (ai-service)
- GET /api/kb/health/ (kb-service)

### 9.4 Kiem tra nhanh chat
- Goi /ai/chat/
- Goi /ai/chat/graph-rag/
- Kiem tra model = "rag-kb"
- Kiem tra graph_context_count > 0 voi graph_hybrid

---

## 10. Uu diem va han che

### 10.1 Uu diem
- Khong phu thuoc LLM runtime ben ngoai cho chat co ban
- Kiem soat duoc logic tra loi va nguon du lieu
- De debug vi output dua tren context ro rang
- Tich hop tot voi recommendation graph hien co

### 10.2 Han che
- Cau van tra loi co the it tu nhien hon chat dung LLM
- Khong co suy luan mo rong ngoai du lieu KB
- Can bo sung logic ranking de cai thien do lien quan trong cac query kho

---

## 11. Checklist test nghiem thu

1. KB collect thanh cong, khong co errors
2. KB recommendation endpoint tra du lieu 200
3. /ai/chat/ tra model = rag-kb, rag_mode = vector_only
4. /ai/chat/graph-rag/ tra model = rag-kb, rag_mode theo input
5. sources khong rong voi truy van hop le
6. graph_context_count > 0 khi dung graph_hybrid va KB co du lieu hanh vi
7. /ai/recommendations/{customer_id}/?mode=hybrid tra du lieu co reason hop le

---

## 12. Huong mo rong tiep theo

1. Bo sung bo nho hoi thoai (session memory) theo customer_id
2. Them bo rank learning-to-rank cho merge vector + graph
3. Bo sung citation format ro hon trong answer
4. Tach layer policy/guardrail cho cac truong hop noi dung nhay cam
5. Co the bat LLM tuy chon trong tuong lai (feature flag), nhung mac dinh van la rag-kb
