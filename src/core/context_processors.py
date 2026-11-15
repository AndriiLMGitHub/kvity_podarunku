from django.core.cache import cache
from modules.shop.models import Category

def global_categories(request):
    # Намагаємося отримати категорії з кешу за унікальним ключем
    categories = cache.get('shop_global_categories')
    
    if categories is None:
        # Якщо в кеші немає, робимо запит до бази даних
        # Обов'язково додаємо .prefetch_related() або .select_related(), якщо є вкладені зв'язки, щоб не викликати N+1
        categories = Category.objects.filter(is_active=True)
        
        # Зберігаємо в кеш на 24 години (у секундах: 60 * 60 * 24)
        cache.set('shop_global_categories', categories, 86400)
        
    return {'categories': categories}