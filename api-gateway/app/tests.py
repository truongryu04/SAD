from django.test import TestCase


class ServiceRegistryViewTests(TestCase):
	def test_service_registry_returns_services_list(self):
		response = self.client.get('/api/services/')

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn('services', payload)
		self.assertIsInstance(payload['services'], list)

	def test_service_registry_contains_customer_register_endpoint(self):
		response = self.client.get('/api/services/')
		payload = response.json()

		found = False
		for service in payload.get('services', []):
			if service.get('service') != 'customer':
				continue
			for endpoint in service.get('endpoints', []):
				if endpoint.get('gateway_path') == '/api/customer/register/':
					found = True
					break
			if found:
				break

		self.assertTrue(found)
