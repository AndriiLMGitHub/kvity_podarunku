from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class BlogCategory(models.Model):
    title = models.CharField(
        max_length=255, 
        verbose_name=_("Назва категорії")
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        verbose_name=_("URL-слаг")
    )

    class Meta:
        verbose_name = _("Категорія статті")
        verbose_name_plural = _("Категорії статей")

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    title = models.CharField(
        max_length=255, 
        verbose_name=_("Заголовок")
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        verbose_name=_("URL-слаг")
    )
    image = models.ImageField(
        upload_to='blog/%Y/%m/', 
        blank=True, 
        null=True, 
        verbose_name=_("Обкладинка")
    )
    # Використовуємо AUTH_USER_MODEL для гнучкості, якщо кастомна модель юзера
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts',
        verbose_name=_("Автор")
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts',
        verbose_name=_("Категорія")
    )
    # Для контенту в реальному проєкті краще використовувати CKEditor або інший RichTextField
    content = models.TextField(
        verbose_name=_("Текст статті")
    )
    is_published = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Опубліковано")
    )
    published_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,  # Індекс для швидкого сортування за датою
        verbose_name=_("Дата публікації")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = _("Стаття")
        verbose_name_plural = _("Статті")
        # Складений індекс: шукаємо тільки опубліковані, сортуємо за датою
        indexes = [
            models.Index(fields=['is_published', '-published_at']),
        ]

    def __str__(self):
        return self.title