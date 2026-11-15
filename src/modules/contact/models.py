from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactMessage(models.Model):
    name = models.CharField(_("Ім'я"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Телефон"), max_length=20, blank=True)
    service_type = models.CharField(_("Тема / Послуга"), max_length=100, blank=True)
    message = models.TextField(_("Повідомлення"))
    created_at = models.DateTimeField(_("Дата створення"), auto_now_add=True)
    is_processed = models.BooleanField(_("Оброблено"), default=False)

    class Meta:
        verbose_name = _("Повідомлення з сайту")
        verbose_name_plural = _("Повідомлення з сайту")
        ordering = ['-created_at']
