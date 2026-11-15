from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="website@example.com",
    ADMIN_EMAIL="owner@example.com",
)
class ContactViewTests(TestCase):
    def setUp(self):
        self.url = reverse("contact")
        self.valid_data = {
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "+380501234567",
            "service_type": "Bouquet",
            "message": "I would like to order a bouquet.",
            "agree": "on",
        }

    def test_contact_page_renders(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contact/contact.html")

    @patch("modules.contact.views.send_mail")
    def test_valid_submission_saves_message_and_sends_notification(self, send_mail):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        message = ContactMessage.objects.get()
        self.assertEqual(message.name, self.valid_data["name"])
        self.assertEqual(message.email, self.valid_data["email"])
        send_mail.assert_called_once()

    @patch("modules.contact.views.send_mail")
    def test_invalid_submission_is_rejected_without_saving(self, send_mail):
        invalid_data = {**self.valid_data, "email": "not-an-email"}

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("email", response.json()["errors"])
        self.assertFalse(ContactMessage.objects.exists())
        send_mail.assert_not_called()

    @patch("modules.contact.views.send_mail")
    def test_submission_requires_consent(self, send_mail):
        invalid_data = {key: value for key, value in self.valid_data.items() if key != "agree"}

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("agree", response.json()["errors"])
        self.assertFalse(ContactMessage.objects.exists())
        send_mail.assert_not_called()

    @patch("modules.contact.views.send_mail", side_effect=OSError("mail service unavailable"))
    def test_mail_failure_does_not_discard_saved_message_or_fail_request(self, send_mail):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(ContactMessage.objects.count(), 1)
        send_mail.assert_called_once()
