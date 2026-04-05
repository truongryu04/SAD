import json
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List

from django.db.models import QuerySet
from pgvector.django import CosineDistance

from .models import ProductVectorIndex


@dataclass
class ProductDocument:
    item_type: str
    item_id: int
    name: str
    brand: str
    price: str
    stock: int
    description: str
    extra: Dict

    @property
    def uid(self) -> str:
        return f"{self.item_type}:{self.item_id}"

    def to_context_line(self) -> str:
        details = []
        if self.item_type == "laptop":
            details.append(f"CPU: {self.extra.get('cpu', 'N/A')}")
            details.append(f"RAM: {self.extra.get('ram_gb', 'N/A')} GB")
            details.append(f"Storage: {self.extra.get('storage_gb', 'N/A')} GB")
        elif self.item_type == "mobile":
            details.append(f"Camera: {self.extra.get('camera_specs', 'N/A')}")
            details.append(f"Screen: {self.extra.get('screen_size', 'N/A')} inch")
            details.append(f"Battery: {self.extra.get('battery_mah', 'N/A')} mAh")

        details_text = " | ".join(details)
        return (
            f"[{self.uid}] {self.name} - brand: {self.brand}, price: {self.price}, "
            f"stock: {self.stock}, description: {self.description or 'N/A'}, {details_text}"
        )

class OllamaClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            },
        }
        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url=f"{self.base_url}/api/generate",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(raw or "{}")
                return str(data.get("response") or "")
        except urllib.error.HTTPError as ex:
            raw = ex.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Ollama HTTPError {ex.code}: {raw}")
        except urllib.error.URLError as ex:
            raise RuntimeError(f"Cannot connect to Ollama: {ex}")


class ProductKnowledgeBase:
    def __init__(self, laptop_service_url: str, mobile_service_url: str) -> None:
        self.laptop_service_url = laptop_service_url.rstrip("/")
        self.mobile_service_url = mobile_service_url.rstrip("/")

    def _fetch_json(self, url: str) -> Dict:
        req = urllib.request.Request(url=url, method="GET", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                return json.loads(raw or "{}")
        except urllib.error.HTTPError as ex:
            raw = ex.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Fetch failed {ex.code} for {url}: {raw}")
        except urllib.error.URLError as ex:
            raise RuntimeError(f"Cannot connect to service for {url}: {ex}")

    def build_documents(self) -> List[ProductDocument]:
        docs: List[ProductDocument] = []

        laptop_payload = self._fetch_json(f"{self.laptop_service_url}/laptops/")
        laptop_items = laptop_payload.get("data") if isinstance(laptop_payload, dict) else []
        if isinstance(laptop_items, list):
            for item in laptop_items:
                item_id = item.get("id")
                if item_id is None:
                    continue
                docs.append(
                    ProductDocument(
                        item_type="laptop",
                        item_id=int(item_id),
                        name=str(item.get("name") or "Unknown"),
                        brand=str(item.get("brand") or "Unknown"),
                        price=str(item.get("price") or "0"),
                        stock=int(item.get("stock") or 0),
                        description=str(item.get("description") or ""),
                        extra={
                            "cpu": item.get("cpu"),
                            "ram_gb": item.get("ram_gb"),
                            "storage_gb": item.get("storage_gb"),
                        },
                    )
                )

        mobile_payload = self._fetch_json(f"{self.mobile_service_url}/mobiles/")
        mobile_items = mobile_payload.get("data") if isinstance(mobile_payload, dict) else []
        if isinstance(mobile_items, list):
            for item in mobile_items:
                item_id = item.get("id")
                if item_id is None:
                    continue
                docs.append(
                    ProductDocument(
                        item_type="mobile",
                        item_id=int(item_id),
                        name=str(item.get("name") or "Unknown"),
                        brand=str(item.get("brand") or "Unknown"),
                        price=str(item.get("price") or "0"),
                        stock=int(item.get("stock") or 0),
                        description=str(item.get("description") or ""),
                        extra={
                            "camera_specs": item.get("camera_specs"),
                            "screen_size": item.get("screen_size"),
                            "battery_mah": item.get("battery_mah"),
                        },
                    )
                )

        return docs


class HashEmbeddingModel:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\w\-\+]+", (text or "").lower())

    def encode(self, text: str) -> List[float]:
        vec = [0.0] * self.dimensions
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for token in tokens:
            h = hash(token)
            idx = abs(h) % self.dimensions
            sign = 1.0 if (h & 1) == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class VectorStoreService:
    def __init__(self, dimensions: int = 256) -> None:
        self.embedding_model = HashEmbeddingModel(dimensions=dimensions)

    def _keyword_overlap(self, query: str, content: str) -> int:
        q_tokens = set(self.embedding_model._tokenize(query))
        c_tokens = set(self.embedding_model._tokenize(content))
        return len(q_tokens.intersection(c_tokens))

    def _build_content_text(self, doc: ProductDocument) -> str:
        return " ".join(
            [
                doc.item_type,
                doc.name,
                doc.brand,
                doc.description,
                str(doc.price),
                str(doc.stock),
                str(doc.extra.get("cpu") or ""),
                str(doc.extra.get("ram_gb") or ""),
                str(doc.extra.get("storage_gb") or ""),
                str(doc.extra.get("camera_specs") or ""),
                str(doc.extra.get("screen_size") or ""),
                str(doc.extra.get("battery_mah") or ""),
            ]
        )

    def upsert_documents(self, docs: List[ProductDocument]) -> None:
        for doc in docs:
            content_text = self._build_content_text(doc)
            embedding = self.embedding_model.encode(content_text)

            ProductVectorIndex.objects.update_or_create(
                item_type=doc.item_type,
                item_id=doc.item_id,
                defaults={
                    "name": doc.name,
                    "brand": doc.brand,
                    "price": str(doc.price),
                    "stock": doc.stock,
                    "description": doc.description,
                    "content_text": content_text,
                    "metadata": doc.extra,
                    "embedding": embedding,
                },
            )

    def retrieve(self, query: str, top_k: int = 8) -> List[ProductDocument]:
        query_embedding = self.embedding_model.encode(query)
        query_tokens = set(self.embedding_model._tokenize(query))
        mobile_tokens = {"mobile", "phone", "dien", "thoai", "camera", "pin"}
        laptop_tokens = {"laptop", "notebook", "ultrabook", "cpu", "ram"}
        queryset: QuerySet[ProductVectorIndex] = (
            ProductVectorIndex.objects.annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[: max(top_k * 5, 20)]
        )

        reranked = []
        for row in queryset:
            keyword_score = self._keyword_overlap(query, row.content_text)
            distance = float(getattr(row, "distance", 1.0) or 1.0)
            type_boost = 0.0
            if query_tokens.intersection(mobile_tokens) and row.item_type == "mobile":
                type_boost += 0.35
            if query_tokens.intersection(laptop_tokens) and row.item_type == "laptop":
                type_boost += 0.35

            final_score = (1.0 - distance) + (0.12 * keyword_score) + type_boost
            reranked.append((final_score, row))

        reranked.sort(key=lambda item: item[0], reverse=True)

        docs: List[ProductDocument] = []
        for _, row in reranked[:top_k]:
            docs.append(
                ProductDocument(
                    item_type=row.item_type,
                    item_id=row.item_id,
                    name=row.name,
                    brand=row.brand,
                    price=row.price,
                    stock=row.stock,
                    description=row.description,
                    extra=row.metadata if isinstance(row.metadata, dict) else {},
                )
            )

        return docs


class Retriever:
    def __init__(self, docs: List[ProductDocument]) -> None:
        self.docs = docs

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\w\-\+]+", text.lower())

    def _doc_text(self, doc: ProductDocument) -> str:
        return " ".join(
            [
                doc.item_type,
                doc.name,
                doc.brand,
                doc.description,
                str(doc.extra.get("cpu") or ""),
                str(doc.extra.get("ram_gb") or ""),
                str(doc.extra.get("storage_gb") or ""),
                str(doc.extra.get("camera_specs") or ""),
                str(doc.extra.get("screen_size") or ""),
                str(doc.extra.get("battery_mah") or ""),
            ]
        ).lower()

    def retrieve(self, query: str, top_k: int = 8) -> List[ProductDocument]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self.docs[:top_k]

        scored = []
        for doc in self.docs:
            text = self._doc_text(doc)
            score = 0.0
            for token in query_tokens:
                if token in text:
                    score += 1.0

            if "laptop" in query_tokens and doc.item_type == "laptop":
                score += 1.5
            if any(x in query_tokens for x in ["điện", "thoại", "mobile", "phone"]) and doc.item_type == "mobile":
                score += 1.5

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]] or self.docs[:top_k]


class NovaShopRAGChatbot:
    def __init__(
        self,
        laptop_service_url: str,
        mobile_service_url: str,
        ollama_base_url: str,
        ollama_model: str = "llama3.1",
    ) -> None:
        self.kb = ProductKnowledgeBase(
            laptop_service_url=laptop_service_url,
            mobile_service_url=mobile_service_url,
        )
        self.vector_store = VectorStoreService(dimensions=256)
        self.llm = OllamaClient(base_url=ollama_base_url, model=ollama_model)

    def _build_prompt(self, customer_question: str, docs: List[ProductDocument]) -> str:
        context_lines = [doc.to_context_line() for doc in docs]
        context_text = "\n".join(context_lines)

        system_instruction = (
            "Bạn là trợ lý bán hàng Nova Shop. "
            "Hãy trả lời bằng tiếng Việt có dấu, ngắn gọn, thân thiện và chỉ dùng thông tin từ ngữ cảnh sản phẩm được cung cấp. "
            "Nếu thiếu dữ liệu thì nói rõ và hỏi thêm nhu cầu của khách hàng."
        )

        response_template = (
            "Mẫu trả lời bắt buộc:\n"
            "1) Lời chào Nova Shop\n"
            "2) Đề xuất sản phẩm phù hợp (2-5 mục), mỗi mục gồm: tên, loại, giá, lý do\n"
            "3) So sánh nhanh nếu có từ 2 sản phẩm trở lên\n"
            "4) Gợi ý hành động tiếp theo (xem chi tiết, thêm giỏ hàng)\n"
            "5) Nếu không tìm thấy sản phẩm phù hợp, nói rõ và đề xuất tiêu chí khác\n"
        )

        return (
            f"{system_instruction}\n\n"
            f"Context products:\n{context_text}\n\n"
            f"Customer question: {customer_question}\n\n"
            f"{response_template}\n"
            "Trả lời bằng tiếng Việt có dấu, gọn và rõ ràng."
        )

    def chat(self, customer_question: str, top_k: int = 8) -> Dict:
        docs = self.kb.build_documents()
        if docs:
            self.vector_store.upsert_documents(docs)

        selected = self.vector_store.retrieve(customer_question, top_k=top_k)
        if not selected:
            raise RuntimeError("Không tìm thấy dữ liệu trong Vector DB để trả lời.")

        prompt = self._build_prompt(customer_question, selected)
        answer = self.llm.generate(prompt)

        return {
            "answer": answer,
            "sources": [
                {
                    "item_type": d.item_type,
                    "item_id": d.item_id,
                    "name": d.name,
                    "brand": d.brand,
                    "price": d.price,
                }
                for d in selected
            ],
            "context_count": len(selected),
        }
