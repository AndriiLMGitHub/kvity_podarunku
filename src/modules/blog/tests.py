from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import BlogCategory, BlogPost


class BlogViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.author = get_user_model().objects.create_user(
            username="blog-author",
            password="test-only-password!2026",
        )
        self.category = BlogCategory.objects.create(
            title="Flower care",
            slug="flower-care",
        )
        self.list_url = reverse("blog_list")

    def create_post(
        self,
        slug,
        *,
        category=None,
        is_published=True,
        published_at=None,
    ):
        return BlogPost.objects.create(
            title=slug.replace("-", " ").title(),
            slug=slug,
            author=self.author,
            category=category,
            content=f"Content for {slug}.",
            is_published=is_published,
            published_at=published_at or timezone.now(),
        )

    def test_blog_list_shows_only_published_posts_that_are_due(self):
        now = timezone.now()
        older = self.create_post(
            "older",
            category=self.category,
            published_at=now - timedelta(days=1),
        )
        newer = self.create_post(
            "newer",
            category=self.category,
            published_at=now,
        )
        self.create_post(
            "draft",
            category=self.category,
            is_published=False,
            published_at=now - timedelta(days=2),
        )
        self.create_post(
            "scheduled",
            category=self.category,
            published_at=now + timedelta(days=1),
        )
        empty_category = BlogCategory.objects.create(
            title="Empty",
            slug="empty",
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["page_obj"]), [newer, older])
        self.assertEqual(
            [category.pk for category in response.context["blog_categories"]],
            [self.category.pk],
        )
        self.assertNotIn(empty_category, response.context["blog_categories"])

    def test_blog_list_filters_by_category(self):
        matching = self.create_post("matching", category=self.category)
        other_category = BlogCategory.objects.create(
            title="Gifts",
            slug="gifts",
        )
        self.create_post("not-matching", category=other_category)

        response = self.client.get(
            self.list_url,
            {"category": self.category.slug},
        )

        self.assertEqual(list(response.context["page_obj"]), [matching])
        self.assertEqual(response.context["current_category"], self.category.slug)

    def test_invalid_page_falls_back_to_first_page(self):
        now = timezone.now()
        for index in range(7):
            self.create_post(
                f"post-{index}",
                published_at=now - timedelta(seconds=index),
            )

        response = self.client.get(self.list_url, {"page": "not-a-number"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)
        self.assertEqual(len(response.context["page_obj"]), 6)

    def test_page_beyond_last_page_returns_not_found(self):
        self.create_post("only-post")

        response = self.client.get(self.list_url, {"page": "99"})

        self.assertEqual(response.status_code, 404)

    def test_published_post_detail_renders_content(self):
        post = self.create_post("published", category=self.category)

        response = self.client.get(
            reverse("blog_detail", kwargs={"slug": post.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], post)
        self.assertContains(response, "Content for published.")

    def test_draft_and_scheduled_post_details_are_hidden(self):
        now = timezone.now()
        draft = self.create_post("hidden-draft", is_published=False)
        scheduled = self.create_post(
            "scheduled-post",
            published_at=now + timedelta(days=1),
        )

        for post in (draft, scheduled):
            with self.subTest(slug=post.slug):
                response = self.client.get(
                    reverse("blog_detail", kwargs={"slug": post.slug})
                )
                self.assertEqual(response.status_code, 404)
