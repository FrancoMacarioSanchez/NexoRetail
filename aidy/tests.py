from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(ALLOWED_HOSTS=["testserver"])
class AidyFileEndpointTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="aidy-test", password="test-password-123"
        )
        self.client.force_login(self.user)
        self.url = reverse("aidy_process_file")

    def test_requires_file(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_returns_validation_error_from_processor(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile("payload.exe", b"nope")
        with patch("aidy.views.process_document", side_effect=ValueError("Formato no admitido.")):
            response = self.client.post(self.url, {"file": upload})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Formato", response.json()["message"])

    @patch("aidy.views.process_document")
    def test_invoice_returns_stock_navigation_without_mutating_stock(self, process_document):
        process_document.return_value = SimpleNamespace(
            tipo="factura_externa",
            productos=[SimpleNamespace(model_dump=lambda: {
                "nombre": "Cemento", "cantidad": 10,
                "costo_unitario": 5000, "precio_unitario": 0, "codigo": "CEM-01"
            })],
            model_dump=lambda: {"tipo": "factura_externa", "productos": []},
        )
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile("factura.pdf", b"%PDF-test", content_type="application/pdf")
        response = self.client.post(self.url, {"file": upload})
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["action"]["type"], "preparar_ingreso_stock")
        self.assertEqual(body["data"]["url"], reverse("ingreso_stock"))
        self.assertEqual(body["data"]["products"][0]["nombre"], "Cemento")
        self.assertIn("No se modificó", body["message"])

    @patch("aidy.views.process_document")
    def test_internal_quote_returns_quote_navigation(self, process_document):
        process_document.return_value = SimpleNamespace(
            tipo="presupuesto_interno", productos=[],
            model_dump=lambda: {"tipo": "presupuesto_interno", "productos": []},
        )
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile("presupuesto.pdf", b"%PDF-test", content_type="application/pdf")
        response = self.client.post(self.url, {"file": upload})
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["action"]["type"], "crear_presupuesto")
        self.assertEqual(body["data"]["url"], reverse("pos_presupuesto"))

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
