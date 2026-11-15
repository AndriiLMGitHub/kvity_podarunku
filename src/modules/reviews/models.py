from django.db import models
from django.utils.translation import gettext_lazy as _


class Testimonial(models.Model):
    author_name = models.CharField(
        max_length=255, 
        verbose_name=_("Ім'я клієнта")
    )
    author_role = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("Статус / Роль"),
        help_text=_("Наприклад: Постійний клієнт")
    )
    text = models.TextField(
        verbose_name=_("Текст відгуку")
    )
    avatar = models.ImageField(
        upload_to='testimonials/%Y/%m/', 
        blank=True, 
        null=True,
        verbose_name=_("Фото клієнта (400x400)")
    )
    is_published = models.BooleanField(
        default=True,
        db_index=True,  # Оптимізація для фільтрації активних відгуків
        verbose_name=_("Опубліковано")
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,  # Оптимізація для сортування каруселі
        verbose_name=_("Порядок сортування")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Дата створення")
    )

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = _("Відгук")
        verbose_name_plural = _("Відгуки клієнтів")
        # Складений індекс для ідеально швидкого запиту без Seq Scan
        indexes = [
            models.Index(fields=['is_published', 'order', '-created_at']),
        ]

    def __str__(self):
        return f"{self.author_name} - {self.text[:30]}..."