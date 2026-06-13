import json
import math
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List

from django.db.models import QuerySet
from pgvector.django import CosineDistance

from .models import ProductVectorIndex
from .recommender import KBGraphRecommender


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
        details_text = " | ".join(
            f"{k}: {v}"
            for k, v in (self.extra or {}).items()
            if v not in (None, "")
        )
        return (
            f"[{self.uid}] {self.name} - brand: {self.brand}, price: {self.price}, "
            f"stock: {self.stock}, description: {self.description or 'N/A'}, {details_text}"
        )


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ProductKnowledgeBase:
    def __init__(self, product_service_url: str) -> None:
        self.product_service_url = (product_service_url or "").rstrip("/")

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

        if self.product_service_url:
            try:
                product_payload = self._fetch_json(f"{self.product_service_url}/api/products/")
                product_items = product_payload.get("data") if isinstance(product_payload, dict) else []
                if not isinstance(product_items, list):
                    product_items = product_payload if isinstance(product_payload, list) else []

                for item in product_items:
                    item_id = item.get("id")
                    if item_id is None:
                        continue

                    stock_value = item.get("stock")
                    try:
                        stock = int(stock_value) if stock_value is not None else 0
                    except (TypeError, ValueError):
                        stock = 0

                    docs.append(
                        ProductDocument(
                            item_type="product",
                            item_id=int(item_id),
                            name=str(item.get("name") or "Unknown"),
                            brand=str(item.get("brand") or "Unknown"),
                            price=str(item.get("base_price") or item.get("price") or "0"),
                            stock=stock,
                            description=str(item.get("description") or ""),
                            extra={},
                        )
                    )
            except RuntimeError:
                pass

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
        extra_text = " ".join(str(v) for v in (doc.extra or {}).values() if v not in (None, ""))
        return " ".join(
            [
                doc.item_type,
                doc.name,
                doc.brand,
                doc.description,
                str(doc.price),
                str(doc.stock),
                extra_text,
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
        queryset: QuerySet[ProductVectorIndex] = (
            ProductVectorIndex.objects.annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[: max(top_k * 5, 20)]
        )

        reranked = []
        for row in queryset:
            keyword_score = self._keyword_overlap(query, row.content_text)
            distance = float(getattr(row, "distance", 1.0) or 1.0)
            final_score = (1.0 - distance) + (0.12 * keyword_score)
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
        extra_text = " ".join(str(v) for v in (doc.extra or {}).values() if v not in (None, ""))
        return " ".join(
            [
                doc.item_type,
                doc.name,
                doc.brand,
                doc.description,
                extra_text,
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

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]] or self.docs[:top_k]


class EcomRAGChatbot:
    def __init__(
        self,
        product_service_url: str,
        kb_service_url: str = "",
    ) -> None:
        self.kb = ProductKnowledgeBase(
            product_service_url=product_service_url,
        )
        self.vector_store = VectorStoreService(dimensions=256)
        self.graph = KBGraphRecommender(kb_service_url) if str(kb_service_url or "").strip() else None

    def _merge_candidates(
        self,
        vector_docs: List[ProductDocument],
        graph_docs: List[ProductDocument],
        top_k: int,
    ) -> List[ProductDocument]:
        merged: Dict[str, ProductDocument] = {}

        for doc in vector_docs:
            merged[doc.uid] = doc

        for doc in graph_docs:
            if doc.uid in merged:
                existing = merged[doc.uid]
                if not existing.description and doc.description:
                    existing.description = doc.description
                if not existing.price and doc.price:
                    existing.price = doc.price
                existing.extra = {
                    **(doc.extra or {}),
                    **(existing.extra or {}),
                }
            else:
                merged[doc.uid] = doc

        return list(merged.values())[:top_k]

    def _to_graph_document(self, row: Dict, local_by_id: Dict[int, ProductDocument]) -> ProductDocument | None:
        product_id = _safe_int(row.get("product_id"), None)
        if product_id is None:
            return None

        local_doc = local_by_id.get(product_id)
        if local_doc:
            copied_extra = dict(local_doc.extra or {})
            copied_extra.update({
                "graph_score": row.get("score"),
                "graph_reason": row.get("reason") or row.get("source") or "graph_retrieval",
            })
            return ProductDocument(
                item_type=local_doc.item_type,
                item_id=local_doc.item_id,
                name=local_doc.name,
                brand=local_doc.brand,
                price=local_doc.price,
                stock=local_doc.stock,
                description=local_doc.description,
                extra=copied_extra,
            )

        return ProductDocument(
            item_type="product",
            item_id=product_id,
            name=str(row.get("name") or f"product-{product_id}"),
            brand=str(row.get("brand") or "Unknown"),
            price=str(row.get("price") or "0"),
            stock=1,
            description=str(row.get("description") or ""),
            extra={
                "graph_score": row.get("score"),
                "graph_reason": row.get("reason") or row.get("source") or "graph_retrieval",
            },
        )

    def _collect_graph_docs(
        self,
        customer_id: int | None,
        product_id: int | None,
        local_by_id: Dict[int, ProductDocument],
        top_k: int,
        mode: str,
        price_range: str = "",
        gender: str = "",
    ) -> List[ProductDocument]:
        if self.graph is None:
            return []

        graph_rows: List[Dict] = []
        mode_value = (mode or "graph_hybrid").strip().lower()

        if mode_value != "vector_only":
            if customer_id and mode_value in ("graph_hybrid", "graph_only", "personalized"):
                graph_rows.extend(
                    self.graph.recommend_personalized(
                        customer_id=customer_id,
                        limit=top_k,
                        price_range=price_range,
                        gender=gender,
                    )
                )

            if product_id and mode_value in ("graph_hybrid", "graph_only", "product"):
                graph_rows.extend(
                    self.graph.recommend_same_category(
                        product_id=product_id,
                        limit=top_k,
                        price_range=price_range,
                        gender=gender,
                    )
                )
                graph_rows.extend(
                    self.graph.recommend_also_bought(
                        product_id=product_id,
                        limit=top_k,
                        price_range=price_range,
                        gender=gender,
                    )
                )

            if not graph_rows:
                graph_rows.extend(
                    self.graph.recommend_top_products(
                        limit=top_k,
                        price_range=price_range,
                        gender=gender,
                    )
                )

        docs: List[ProductDocument] = []
        seen = set()
        for row in graph_rows:
            doc = self._to_graph_document(row, local_by_id=local_by_id)
            if doc is None or doc.uid in seen:
                continue
            seen.add(doc.uid)
            docs.append(doc)
            if len(docs) >= top_k:
                break

        return docs

    def _parse_price_value(self, price: str) -> float:
        text = str(price or "")
        normalized = re.sub(r"[^0-9.,]", "", text).replace(",", "")
        try:
            return float(normalized) if normalized else 0.0
        except ValueError:
            return 0.0

    def _fallback_answer(self, customer_question: str, docs: List[ProductDocument], reason: str) -> str:
        q = customer_question.lower()
        wants_most_expensive = any(tok in q for tok in ["đắt nhất", "dat nhat", "cao nhất", "max"])
        wants_cheapest = any(tok in q for tok in ["rẻ nhất", "re nhat", "thấp nhất", "min"])

        filtered = docs

        if wants_most_expensive:
            filtered = sorted(filtered, key=lambda d: self._parse_price_value(d.price), reverse=True)
        elif wants_cheapest:
            filtered = sorted(filtered, key=lambda d: self._parse_price_value(d.price))

        picks = filtered[:3]
        if not picks:
            return (
                "Nova Shop chưa có đủ dữ liệu sản phẩm để tư vấn lúc này. "
                "Bạn thử nêu rõ nhu cầu: tầm giá, hãng, RAM hoặc camera nhé."
            )

        lines = []
        for idx, p in enumerate(picks, start=1):
            lines.append(
                f"{idx}. {p.name} - giá: {p.price}, hãng: {p.brand}, tồn kho: {p.stock}"
            )

        reason_note = (
            "Trả lời hiện tại dựa trên dữ liệu KB/RAG đang có. "
            "Bạn có thể hỏi thêm theo hãng, tầm giá hoặc nhu cầu để mình lọc chính xác hơn."
        )
        return "\n".join(
            [
                "Xin chào, Nova Shop gợi ý nhanh cho bạn:",
                *lines,
                "Bạn muốn mình lọc tiếp theo hãng hoặc tầm giá cụ thể không?",
                reason_note,
            ]
        )

    def _sorted_docs_for_question(self, customer_question: str, docs: List[ProductDocument]) -> List[ProductDocument]:
        scored = self._rank_docs(customer_question, docs)
        return [row["doc"] for row in scored]

    def _normalize_text(self, text: str) -> str:
        raw = str(text or "").lower()
        normalized = unicodedata.normalize("NFD", raw)
        no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return no_accents

    def _detect_price_band(self, text: str) -> str:
        t = self._normalize_text(text)
        if any(token in t for token in ["gia re", "re", "budget", "sinh vien", "duoi 10", "<10"]):
            return "budget"
        if any(token in t for token in ["tam trung", "trung cap", "mid", "10-20", "10 den 20"]):
            return "mid"
        if any(token in t for token in ["cao cap", "premium", "flagship", "tren 20", ">20"]):
            return "premium"
        return ""

    def _extract_budget_numbers(self, text: str) -> Dict[str, float | None]:
        t = self._normalize_text(text)
        nums = [float(val.replace(",", ".")) for val in re.findall(r"\d+(?:[\.,]\d+)?", t)]
        if not nums:
            return {"min": None, "max": None}

        # Treat short numbers as million VND for user-friendly Vietnamese queries.
        scaled = [num * 1_000_000 if num < 1000 else num for num in nums]

        has_under = any(token in t for token in ["duoi", "toi da", "max", "<"])
        has_over = any(token in t for token in ["tren", "tu", "min", ">"])

        if len(scaled) >= 2 and any(token in t for token in ["den", "-", "toi"]):
            low, high = min(scaled), max(scaled)
            return {"min": low, "max": high}

        if has_under:
            return {"min": None, "max": scaled[0]}
        if has_over:
            return {"min": scaled[0], "max": None}

        return {"min": None, "max": scaled[0]}

    def _extract_query_signals(self, customer_question: str) -> Dict:
        q = self._normalize_text(customer_question)
        tokens = [token for token in re.findall(r"[a-z0-9\+\-]+", q) if len(token) > 1]

        known_brands = [
            "apple", "iphone", "samsung", "xiaomi", "oppo", "vivo", "realme",
            "dell", "hp", "lenovo", "asus", "acer", "msi", "macbook",
        ]
        brand_tokens = [brand for brand in known_brands if brand in q]

        type_keywords = {
            "laptop": ["laptop", "notebook", "ultrabook", "macbook"],
            "mobile": ["dien thoai", "phone", "smartphone", "iphone", "android"],
            "gaming": ["gaming", "choi game", "fps", "esport"],
            "office": ["van phong", "hoc tap", "study", "office"],
        }
        matched_types = []
        for key, variants in type_keywords.items():
            if any(variant in q for variant in variants):
                matched_types.append(key)

        budget = self._extract_budget_numbers(customer_question)
        is_programming_need = any(
            token in q
            for token in ["lap trinh", "coding", "programming", "developer", "dev", "code"]
        )

        return {
            "normalized": q,
            "tokens": tokens,
            "brands": brand_tokens,
            "types": matched_types,
            "price_band": self._detect_price_band(customer_question),
            "budget_min": budget["min"],
            "budget_max": budget["max"],
            "is_programming_need": is_programming_need,
            "wants_most_expensive": any(tok in q for tok in ["dat nhat", "cao nhat", "max"]),
            "wants_cheapest": any(tok in q for tok in ["re nhat", "thap nhat", "min", "gia thap"]),
        }

    def _doc_text(self, doc: ProductDocument) -> str:
        return self._normalize_text(
            " ".join(
                [
                    str(doc.item_type or ""),
                    str(doc.name or ""),
                    str(doc.brand or ""),
                    str(doc.description or ""),
                ]
            )
        )

    def _score_doc(self, doc: ProductDocument, signals: Dict) -> Dict:
        score = 0.0
        reasons: List[str] = []

        text = self._doc_text(doc)
        price = self._parse_price_value(doc.price)
        graph_score_raw = (doc.extra or {}).get("graph_score")
        try:
            graph_score = float(graph_score_raw or 0.0)
        except (TypeError, ValueError):
            graph_score = 0.0

        # 1) Keyword overlap signal
        overlap = 0
        for token in signals["tokens"]:
            if token in text:
                overlap += 1
        if overlap > 0:
            score += min(overlap, 6) * 1.1
            reasons.append("khop tu khoa")

        # 2) Brand and type signals
        brand_hit = any(brand in text for brand in signals["brands"])
        if brand_hit:
            score += 2.0
            reasons.append("dung hang ban yeu cau")

        type_hit = False
        for wanted_type in signals["types"]:
            if wanted_type == "laptop" and ("laptop" in text or "notebook" in text or "macbook" in text):
                type_hit = True
            if wanted_type == "mobile" and ("mobile" in text or "phone" in text or "iphone" in text):
                type_hit = True
            if wanted_type in ("gaming", "office") and wanted_type in text:
                type_hit = True
        if type_hit:
            score += 1.6
            reasons.append("dung nhu cau su dung")

        if signals.get("is_programming_need"):
            if "laptop" in text or "notebook" in text or "macbook" in text:
                score += 1.5
                reasons.append("phu hop nhu cau lap trinh")
            elif "mobile" in text or "phone" in text:
                score -= 0.8

        # 3) Price-based signal
        if signals["price_band"]:
            if signals["price_band"] == "budget" and 0 < price < 10_000_000:
                score += 1.5
                reasons.append("phu hop tam gia budget")
            if signals["price_band"] == "mid" and 10_000_000 <= price <= 20_000_000:
                score += 1.5
                reasons.append("phu hop tam gia mid")
            if signals["price_band"] == "premium" and price > 20_000_000:
                score += 1.5
                reasons.append("phu hop tam gia premium")

        if signals["budget_min"] is not None and price > 0:
            if price >= float(signals["budget_min"]):
                score += 0.9
            else:
                score -= 1.2

        if signals["budget_max"] is not None and price > 0:
            if price <= float(signals["budget_max"]):
                score += 1.2
                reasons.append("nam trong ngan sach")
            else:
                score -= 1.8

        # 4) Graph relevance signal
        if graph_score > 0:
            score += min(graph_score / 10.0, 3.0)
            reasons.append("duoc uu tien boi hanh vi tren KB graph")

        # 5) Intent: cheapest / most expensive
        if signals["wants_cheapest"] and price > 0:
            score += max(0.0, 2.0 - (price / 20_000_000))
        if signals["wants_most_expensive"] and price > 0:
            score += min(2.0, price / 20_000_000)

        # 6) Penalize unavailable stock when we have stock info
        if doc.stock is not None and int(doc.stock) <= 0:
            score -= 0.4

        return {
            "doc": doc,
            "score": round(score, 6),
            "reasons": reasons,
        }

    def _rank_docs(self, customer_question: str, docs: List[ProductDocument]) -> List[Dict]:
        signals = self._extract_query_signals(customer_question)
        scored = [self._score_doc(doc, signals) for doc in docs]
        scored.sort(key=lambda row: (float(row["score"]), self._parse_price_value(row["doc"].price)), reverse=True)

        if signals["wants_cheapest"]:
            scored.sort(
                key=lambda row: (
                    -float(row["score"]),
                    self._parse_price_value(row["doc"].price) if self._parse_price_value(row["doc"].price) > 0 else 10**18,
                )
            )
        return scored

    def _source_reason_text(self, doc: ProductDocument, rag_mode: str) -> str:
        graph_reason = str((doc.extra or {}).get("graph_reason") or "").strip()
        if graph_reason:
            return f"phu hop theo KB graph ({graph_reason})"
        if rag_mode == "vector_only":
            return "khop voi tu khoa truy van trong KB"
        return "khop voi ngu canh truy van"

    @staticmethod
    def _format_vnd(price_value: float) -> str:
        if price_value <= 0:
            return "Chua ro"
        return f"{int(round(price_value)):,}".replace(",", ".") + " VND"

    def _build_rule_based_answer(self, customer_question: str, docs: List[ProductDocument], rag_mode: str) -> str:
        ranked_rows = self._rank_docs(customer_question, docs)
        signals = self._extract_query_signals(customer_question)

        filtered_rows = ranked_rows
        wants_laptop_focus = signals.get("is_programming_need") or (
            "laptop" in signals.get("types", []) and "mobile" not in signals.get("types", [])
        )
        if wants_laptop_focus:
            laptop_rows = [
                row for row in ranked_rows
                if "laptop" in str((row["doc"].item_type or "")).lower()
                or "laptop" in self._doc_text(row["doc"])
                or "notebook" in self._doc_text(row["doc"])
                or "macbook" in self._doc_text(row["doc"])
            ]
            if laptop_rows:
                filtered_rows = laptop_rows

        if "mobile" in signals.get("types", []) and "laptop" not in signals.get("types", []):
            mobile_rows = [
                row for row in ranked_rows
                if "mobile" in str((row["doc"].item_type or "")).lower()
                or "phone" in self._doc_text(row["doc"])
                or "iphone" in self._doc_text(row["doc"])
            ]
            if mobile_rows:
                filtered_rows = mobile_rows

        picks = filtered_rows[: min(5, len(filtered_rows))]
        if not picks:
            return self._fallback_answer(customer_question, docs, "no_context")

        lines = ["Chao mung ban den voi Nova Shop!"]

        intro = ["Duoi day la cac lua chon phu hop nhat"]
        if signals.get("budget_max"):
            intro.append(f"trong tam ngan sach den khoang {self._format_vnd(float(signals['budget_max']))}")
        if signals.get("is_programming_need"):
            intro.append("uu tien cho nhu cau lap trinh")
        lines.append(", ".join(intro) + ":")

        for idx, row in enumerate(picks, start=1):
            p = row["doc"]
            reason_parts = []
            if row["reasons"]:
                reason_parts.append("; ".join(row["reasons"][:2]))
            reason_parts.append(self._source_reason_text(p, rag_mode))
            reason = " | ".join(reason_parts)
            item_type_raw = (p.item_type or "product").lower()
            item_type = "Laptop" if "laptop" in item_type_raw else ("Dien thoai" if "mobile" in item_type_raw else "San pham")
            formatted_price = self._format_vnd(self._parse_price_value(p.price))
            lines.append(
                f"{idx}. {p.name} ({item_type}) - Gia: {formatted_price}, Hang: {p.brand}, Ly do: {reason}."
            )

        if len(picks) >= 2:
            first = picks[0]["doc"]
            second = picks[1]["doc"]
            first_price = self._format_vnd(self._parse_price_value(first.price))
            second_price = self._format_vnd(self._parse_price_value(second.price))
            lines.append(
                "So sanh nhanh: "
                f"{first.name} ({first_price}) va {second.name} ({second_price}) deu la lua chon tot; ban co the chon theo thuong hieu va ngan sach uu tien."
            )

        lines.append("Ban muon minh loc sau hon theo RAM, CPU, thuong hieu hay muc gia cu the khong?")
        return "\n".join(lines)

    def chat(
        self,
        customer_question: str,
        top_k: int = 8,
        customer_id: int | None = None,
        product_id: int | None = None,
        rag_mode: str = "graph_hybrid",
        price_range: str = "",
        gender: str = "",
    ) -> Dict:
        docs = self.kb.build_documents()
        if docs:
            self.vector_store.upsert_documents(docs)

        local_by_id = {doc.item_id: doc for doc in docs if doc.item_type == "product"}

        selected_vector = [] if rag_mode == "graph_only" else self.vector_store.retrieve(customer_question, top_k=top_k)
        selected_graph = self._collect_graph_docs(
            customer_id=customer_id,
            product_id=product_id,
            local_by_id=local_by_id,
            top_k=top_k,
            mode=rag_mode,
            price_range=price_range,
            gender=gender,
        )

        selected = self._merge_candidates(selected_vector, selected_graph, top_k=top_k)
        if not selected:
            answer = self._fallback_answer(
                customer_question,
                [],
                "Không truy xuất được dữ liệu sản phẩm từ các service nguồn",
            )
            return {
                "answer": answer,
                "fallback_used": True,
                "sources": [],
                "context_count": 0,
                "vector_context_count": 0,
                "graph_context_count": 0,
            }

        ranked_rows = self._rank_docs(customer_question, selected)
        answer = self._build_rule_based_answer(customer_question, selected, rag_mode=rag_mode)
        top_ranked = ranked_rows[: min(top_k, len(ranked_rows))]

        return {
            "answer": answer,
            "fallback_used": False,
            "sources": [
                {
                    "item_type": row["doc"].item_type,
                    "item_id": row["doc"].item_id,
                    "name": row["doc"].name,
                    "brand": row["doc"].brand,
                    "price": row["doc"].price,
                    "score": row["score"],
                    "reasons": row["reasons"],
                    "graph_reason": (row["doc"].extra or {}).get("graph_reason"),
                }
                for row in top_ranked
            ],
            "context_count": len(top_ranked),
            "vector_context_count": len(selected_vector),
            "graph_context_count": len(selected_graph),
            "rag_mode": rag_mode,
        }
