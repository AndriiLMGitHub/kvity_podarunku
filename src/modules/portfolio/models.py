from django.db import models
from django.utils.translation import gettext_lazy as _


class PortfolioWork(models.Model):
    title = models.CharField(
        max_length=255, 
        verbose_name=_("Назва роботи")
    )
    image = models.ImageField(
        upload_to='portfolio/%Y/%m/', 
        verbose_name=_("Зображення")
    )
    is_published = models.BooleanField(
        default=True,
        db_index=True,  # Оптимізація для .filter(is_published=True)
        verbose_name=_("Опубліковано")
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,  # Оптимізація для сортування
        verbose_name=_("Порядок сортування")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Дата додавання")
    )

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _("Робота портфоліо")
        verbose_name_plural = _("Наші роботи")
        # Складений індекс для швидкого доступу при рендері списку
        indexes = [
            models.Index(fields=['is_published', 'order', '-created_at']),
        ]

    def __str__(self):
        return self.title
    