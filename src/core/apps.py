from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    name = 'core'
    
    def ready(self):
        # Імпортуємо сигнали при старті додатку
        import core.signals
