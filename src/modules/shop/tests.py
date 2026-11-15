from django.test import TestCase

from .models import Category


class GetAllProductsViewTests(TestCase):
    def test_renders_index_with_active_root_categories_in_sort_order(self):
        second = Category.objects.create(
            name="Second",
            slug="second",
            is_active=True,
            sort_order=2,
        )
        Category.objects.create(
            name="Inactive root",
            slug="inactive-root",
            is_active=False,
            sort_order=0,
        )
        Category.objects.create(
            name="Active child",
            slug="active-child",
            parent=second,
            is_active=True,
            sort_order=0,
        )
        first = Category.objects.create(
            name="First",
            slug="first",
            is_active=True,
            sort_order=1,
        )

        response = self.client.get("/uk/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(
            list(response.context["categories"]),
            [first, second],
        )

    def test_renders_index_when_there_are_no_active_root_categories(self):
        Category.objects.create(
            name="Inactive root",
            slug="inactive-root",
            is_active=False,
        )

        response = self.client.get("/uk/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(list(response.context["categories"]), [])
