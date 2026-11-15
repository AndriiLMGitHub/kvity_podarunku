import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase


class EnsureSuperuserCommandTests(TestCase):
    def set_credentials(self, username="", email="", password=""):
        return patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": username,
                "DJANGO_SUPERUSER_EMAIL": email,
                "DJANGO_SUPERUSER_PASSWORD": password,
            },
        )

    def test_skips_when_credentials_are_unset(self):
        with self.set_credentials():
            call_command("ensure_superuser")

        self.assertFalse(get_user_model().objects.exists())

    def test_creates_superuser_once_without_resetting_existing_password(self):
        credentials = self.set_credentials(
            username="bootstrap-admin",
            email="bootstrap@example.com",
            password="qV7!aP9#tR2$mN5&",
        )
        with credentials:
            call_command("ensure_superuser")
            user = get_user_model().objects.get(username="bootstrap-admin")

            self.assertTrue(user.is_staff)
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.check_password("qV7!aP9#tR2$mN5&"))

            user.set_password("changed-after-bootstrap!2026")
            user.save(update_fields=["password"])
            call_command("ensure_superuser")

        user.refresh_from_db()
        self.assertTrue(user.check_password("changed-after-bootstrap!2026"))

    def test_does_not_promote_existing_regular_user(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="existing-user",
            email="existing@example.com",
            password="test-only-password!2026",
        )

        with self.set_credentials(
            username="existing-user",
            email="existing@example.com",
            password="qV7!aP9#tR2$mN5&",
        ):
            with self.assertRaises(CommandError):
                call_command("ensure_superuser")

        user = user_model.objects.get(username="existing-user")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_rejects_partial_credentials(self):
        with self.set_credentials(username="bootstrap-admin"):
            with self.assertRaises(CommandError):
                call_command("ensure_superuser")
