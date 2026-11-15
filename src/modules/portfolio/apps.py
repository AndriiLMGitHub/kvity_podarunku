from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PortfolioConfig(AppConfig):
    name = 'modules.portfolio'
    label = 'portfolio'

    verbose_name = _('Портфоліо')
    verbose_name_plural = _('Портфоліо')
