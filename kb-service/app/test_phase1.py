from django.urls import reverse
from rest_framework.test import APITestCase
from app.models import KBProduct, KBCategory, KBInventory

class KBPhase1SmokeTest(APITestCase):
    def setUp(self):
        cat = KBCategory.objects.create(external_id=1, name="Laptop", description="", raw_payload={})
        KBProduct.objects.create(
            external_id=101,
            name="Laptop ABC",
            description="Good laptop",
            brand="BrandX",
            category_external_id=1,
            category_name="Laptop",
            base_price=10000000,
            status="ACTIVE",
            normalized_text="laptop abc good laptop brandx laptop 10000000 active",
            raw_payload={},
        )
        KBInventory.objects.create(external_id=201, variant_id=101, quantity=5, reserved_quantity=1, raw_payload={})

    def test_health(self):
        url = reverse("kb-health")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("counts", resp.data)

    def test_semantic_search(self):
        url = reverse("kb-search-semantic")
        resp = self.client.post(url, {"query": "laptop abc"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["data"][0]["product_id"], 101)
        self.assertIn("quantity", resp.data["data"][0])

    def test_sync_status(self):
        url = reverse("kb-sync-status")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("checkpoints", resp.data)
