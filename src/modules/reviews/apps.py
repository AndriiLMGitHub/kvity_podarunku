from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReviewsConfig(AppConfig):
    name = 'modules.reviews'
    label = 'reviews'

    verbose_name = _('Відгуки')
    verbose_name_plural = _('Відгуки')
