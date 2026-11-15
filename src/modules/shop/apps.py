from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ShopConfig(AppConfig):
    name = 'modules.shop'
    label = 'shop'

    verbose_name = _('Магазин')
    verbose_name_plural = _('Магазини')
    
