from django.test import TestCase

from .models import Testimonial


class TestimonialTests(TestCase):
    def test_published_testimonials_follow_configured_order(self):
        second = Testimonial.objects.create(
            author_name="Second customer",
            text="Second review.",
            order=2,
        )
        hidden = Testimonial.objects.create(
            author_name="Hidden customer",
            text="Unpublished review.",
            order=0,
            is_published=False,
        )
        first = Testimonial.objects.create(
            author_name="First customer",
            text="First review.",
            order=1,
        )

        testimonials = Testimonial.objects.filter(is_published=True)

        self.assertEqual(list(testimonials), [first, second])
        self.assertNotIn(hidden, testimonials)
