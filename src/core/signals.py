from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from modules.shop.models import Category

@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    # Видаляємо кеш, щойно відбулися будь-які зміни в категоріях
    cache.delete('shop_global_categories')