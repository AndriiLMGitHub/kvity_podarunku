from django.test import TestCase

from .models import PortfolioWork


class PortfolioWorkTests(TestCase):
    def test_published_works_follow_configured_order(self):
        second = PortfolioWork.objects.create(
            title="Second work",
            image="",
            order=2,
        )
        hidden = PortfolioWork.objects.create(
            title="Hidden work",
            image="",
            order=0,
            is_published=False,
        )
        first = PortfolioWork.objects.create(
            title="First work",
            image="",
            order=1,
        )

        works = PortfolioWork.objects.filter(is_published=True)

        self.assertEqual(list(works), [first, second])
        self.assertNotIn(hidden, works)
