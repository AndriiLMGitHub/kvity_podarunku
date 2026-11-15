from datetime import timedelta
import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from modules.blog.models import BlogPost
from modules.portfolio.models import PortfolioWork
from modules.reviews.models import Testimonial
from modules.shop.models import Category


class HomeViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_homepage_shows_active_and_published_content(self):
        root_category = Category.objects.create(name="Root", slug="root", sort_order=1)
        Category.objects.create(
            name="Child",
            slug="child",
            parent=root_category,
            sort_order=0,
        )
        Category.objects.create(
            name="Inactive",
            slug="inactive",
            is_active=False,
        )

        first_work = PortfolioWork.objects.create(
            title="First work",
            image="",
            order=1,
        )
        second_work = PortfolioWork.objects.create(
            title="Second work",
            image="",
            order=2,
        )
        PortfolioWork.objects.create(
            title="Hidden work",
            image="",
            is_published=False,
        )

        first_testimonial = Testimonial.objects.create(
            author_name="First customer",
            text="A great bouquet.",
            order=1,
        )
        Testimonial.objects.create(
            author_name="Hidden customer",
            text="Not published.",
            is_published=False,
        )

        author = get_user_model().objects.create_user(
            username="blog-author",
            password="test-only-password!2026",
        )
        now = timezone.now()
        older_post = BlogPost.objects.create(
            title="Older post",
            slug="older-post",
            author=author,
            content="Older content.",
            published_at=now - timedelta(days=1),
        )
        latest_post = BlogPost.objects.create(
            title="Latest post",
            slug="latest-post",
            author=author,
            content="Latest content.",
            published_at=now,
        )
        BlogPost.objects.create(
            title="Scheduled post",
            slug="scheduled-post",
            author=author,
            content="Not yet published.",
            published_at=now + timedelta(days=1),
        )
        BlogPost.objects.create(
            title="Draft post",
            slug="draft-post",
            author=author,
            content="Draft content.",
            is_published=False,
        )

        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["categories"]), [root_category])
        self.assertEqual(
            list(response.context["portfolio_works"]),
            [first_work, second_work],
        )
        self.assertEqual(
            list(response.context["latest_posts"]),
            [latest_post, older_post],
        )
        self.assertEqual(
            list(response.context["testimonials"]),
            [first_testimonial],
        )

    def test_about_page_renders(self):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")


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
