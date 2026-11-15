import os

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial superuser from environment variables if configured."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")

        if not username and not email and not password:
            self.stdout.write("Initial superuser credentials are not configured; skipping.")
            return

        if not username or not email or not password:
            raise CommandError(
                "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and "
                "DJANGO_SUPERUSER_PASSWORD together, or leave all three unset."
            )

        user_model = get_user_model()
        manager = user_model._default_manager
        username_lookup = {user_model.USERNAME_FIELD: username}

        existing_user = manager.filter(**username_lookup).first()
        if existing_user is not None:
            self._report_existing_user(existing_user)
            return

        try:
            validate_password(
                password,
                user=user_model(
                    **{
                        user_model.USERNAME_FIELD: username,
                        user_model.EMAIL_FIELD: email,
                    }
                ),
            )
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        user, created = manager.get_or_create(
            **username_lookup,
            defaults={
                user_model.EMAIL_FIELD: manager.normalize_email(email),
                "password": make_password(password),
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if not created:
            self._report_existing_user(user)
            return

        self.stdout.write(self.style.SUCCESS("Initial superuser created."))

    def _report_existing_user(self, user):
        if not user.is_staff or not user.is_superuser:
            raise CommandError(
                "A non-superuser account already uses the configured username. "
                "Choose another DJANGO_SUPERUSER_USERNAME."
            )
        self.stdout.write("Initial superuser already exists; it was not changed.")
