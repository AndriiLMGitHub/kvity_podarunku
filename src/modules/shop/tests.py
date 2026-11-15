from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Product, ProductImage


class ShopViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name="Flowers", slug="flowers")

    def create_product(self, slug, category=None, price="10.00", is_active=True):
        return Product.objects.create(
            category=category or self.category,
            sku=slug.upper(),
            name=slug.replace("-", " ").title(),
            slug=slug,
            price=Decimal(price),
            is_active=is_active,
        )

    def test_product_list_filters_inactive_products_and_sorts_by_price(self):
        expensive = self.create_product("expensive", price="25.00")
        cheap = self.create_product("cheap", price="5.00")
        self.create_product("hidden", price="1.00", is_active=False)

        response = self.client.get(reverse("product_list"), {"sort": "price_asc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["products"]),
            [cheap, expensive],
        )

    def test_category_list_includes_active_children_only(self):
        active_child = Category.objects.create(
            name="Roses",
            slug="roses",
            parent=self.category,
        )
        inactive_child = Category.objects.create(
            name="Hidden child",
            slug="hidden-child",
            parent=self.category,
            is_active=False,
        )
        other_category = Category.objects.create(name="Gifts", slug="gifts")
        root_product = self.create_product("root-product")
        child_product = self.create_product("child-product", category=active_child)
        self.create_product("inactive-child-product", category=inactive_child)
        self.create_product("other-product", category=other_category)

        response = self.client.get(
            reverse("category_detail", kwargs={"category_slug": self.category.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["products"]),
            {root_product, child_product},
        )

    def test_invalid_category_returns_not_found(self):
        response = self.client.get(
            reverse("category_detail", kwargs={"category_slug": "missing"})
        )

        self.assertEqual(response.status_code, 404)

    def test_invalid_page_uses_first_page_and_out_of_range_uses_last(self):
        for index in range(13):
            self.create_product(f"product-{index:02d}")

        first_page = self.client.get(reverse("product_list"), {"page": "not-a-number"})
        last_page = self.client.get(reverse("product_list"), {"page": "999"})

        self.assertEqual(first_page.context["page_obj"].number, 1)
        self.assertEqual(len(first_page.context["products"]), 12)
        self.assertEqual(last_page.context["page_obj"].number, 2)
        self.assertEqual(len(last_page.context["products"]), 1)

    def test_product_detail_only_shows_active_related_products(self):
        current = self.create_product("current")
        related_products = [
            self.create_product(f"related-{index}")
            for index in range(5)
        ]
        inactive = self.create_product("inactive-related", is_active=False)
        other_category = Category.objects.create(name="Gifts", slug="gifts")
        self.create_product("other-category", category=other_category)

        for index, product in enumerate(related_products):
            Product.objects.filter(pk=product.pk).update(
                created_at=timezone.now() + timedelta(seconds=index)
            )

        response = self.client.get(
            reverse("product_detail", kwargs={"slug": current.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["related_products"]),
            list(reversed(related_products[1:])),
        )
        self.assertNotIn(inactive, response.context["related_products"])

    def test_inactive_product_detail_returns_not_found(self):
        inactive = self.create_product("inactive", is_active=False)

        response = self.client.get(
            reverse("product_detail", kwargs={"slug": inactive.slug})
        )

        self.assertEqual(response.status_code, 404)


class ProductImageTests(TestCase):
    def test_saving_main_image_demotes_previous_main_image(self):
        category = Category.objects.create(name="Flowers", slug="flowers")
        product = Product.objects.create(
            category=category,
            sku="FLOWER-1",
            name="Rose",
            slug="rose",
            price=Decimal("10.00"),
        )

        first = ProductImage.objects.create(
            product=product,
            image="products/first.jpg",
            is_main=True,
        )
        second = ProductImage.objects.create(
            product=product,
            image="products/second.jpg",
            is_main=True,
        )
        secondary = ProductImage.objects.create(
            product=product,
            image="products/secondary.jpg",
            is_main=False,
        )

        first.refresh_from_db()
        second.refresh_from_db()
        secondary.refresh_from_db()
        self.assertFalse(first.is_main)
        self.assertTrue(second.is_main)
        self.assertFalse(secondary.is_main)
