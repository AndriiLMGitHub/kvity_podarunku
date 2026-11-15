import logging
from django.template.backends import django
from django.utils import timezone
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.cache import cache

from .models import BlogPost, BlogCategory


logger = logging.getLogger(__name__)


def blog_list_view(request: HttpRequest) -> HttpResponse:
    """
    Відображає список опублікованих статей блогу з підтримкою пагінації 
    та фільтрації за категоріями.
    """
    
    # 1. ФОРМУВАННЯ QUERYSET (Список статей)
    try:
        # Базовий запит: опубліковані статті, дата яких вже настала.
        # select_related миттєво підтягує автора та категорію (запобігання N+1).
        posts = BlogPost.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'category')
        
        # Фільтрація за категорією з GET-параметра (?category=slug)
        category_slug = request.GET.get('category')
        if category_slug:
            posts = posts.filter(category__slug=category_slug)
            logger.info(f"Користувач фільтрує блог за категорією: {category_slug}")
            
    except Exception as e:
        logger.error(f"Критична помилка бази даних при отриманні статей: {e}", exc_info=True)
        posts = BlogPost.objects.none()
        category_slug = None


    # 2. ФОРМУВАННЯ КАТЕГОРІЙ (Для сайдбару/фільтрів)
    try:
        # Беремо лише ті категорії, в яких є реальні (опубліковані) статті
        active_categories = BlogCategory.objects.annotate(
            published_count=Count(
                'posts', 
                filter=Q(posts__is_published=True, posts__published_at__lte=timezone.now())
            )
        ).filter(published_count__gt=0)
    except Exception as e:
        logger.error(f"Помилка при формуванні списку категорій: {e}")
        active_categories = []


    # 3. ПАГІНАЦІЯ (Ручний та надійний контроль)
    paginator = Paginator(posts, 6)  # 6 статей на сторінку
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Якщо передали текст або порожньо (?page=abc), віддаємо першу сторінку
        page_obj = paginator.page(1)
    except EmptyPage as e:
        # Якщо сторінка поза межами (наприклад, ?page=9999), логуємо і віддаємо 404
        logger.warning(f"Спроба доступу до неіснуючої сторінки блогу: {page_number}. {e}")
        raise Http404("Цієї сторінки не існує.")


    # 4. ФОРМУВАННЯ КОНТЕКСТУ ТА РЕНДЕР
    context = {
        'page_obj': page_obj,  # Саме цей об'єкт ми ітеруємо в шаблоні {% for post in page_obj %}
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(), # Прапорець для показу блоку пагінації
        'blog_categories': active_categories,
        'current_category': category_slug or '',
    }

    return render(request, 'blog/blog_list.html', context)


def blog_detail_view(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Відображає деталі однієї статті блогу.
    Оптимізовано: кешування агрегації, захист від маскування 500 помилок.
    """
    
    # 1. ОТРИМАННЯ СТАТТІ (Без кешування, бо контент/перегляди оновлюються часто)
    try:
        post = BlogPost.objects.select_related('author', 'category').get(
            slug=slug,
            is_published=True,
            published_at__lte=timezone.now()
        )
    except BlogPost.DoesNotExist:
        # Логуємо як warning, бо це штатна ситуація (бите посилання або бот)
        logger.warning(f"404: Спроба доступу до неіснуючої або прихованої статті [slug: {slug}]")
        raise Http404("Стаття не знайдена або ще не опублікована.")
    except Exception as e:
        # Логуємо як error з повним трейсом. 
        # НЕ викидаємо 404. Дозволяємо винятку піднятися вище, щоб Django віддав 500 помилку.
        logger.error(f"Критична помилка БД при отриманні статті [slug: {slug}]: {e}", exc_info=True)
        raise

    # 2. ОТРИМАННЯ КАТЕГОРІЙ (Кешування на 1 годину)
    cache_key = 'blog_sidebar_categories'
    active_categories = cache.get(cache_key)

    if active_categories is None:
        try:
            qs = BlogCategory.objects.annotate(
                published_count=Count(
                    'posts', 
                    filter=Q(posts__is_published=True, posts__published_at__lte=timezone.now())
                )
            ).filter(published_count__gt=0)
            
            # list() примусово виконує SQL-запит ДО запису в кеш.
            # Не можна кешувати сирий об'єкт QuerySet, бо він лінивий (lazy).
            active_categories = list(qs)
            
            # Зберігаємо в кеш на 3600 секунд (1 година)
            cache.set(cache_key, active_categories, 3600)
            logger.info("Категорії блогу успішно згенеровані та закешовані.")
            
        except Exception as e:
            logger.error(f"Помилка при агрегації категорій: {e}", exc_info=True)
            active_categories = []

    # 3. РЕНДЕР
    context = {
        'post': post,
        'blog_categories': active_categories,
    }

    return render(request, 'blog/blog_detail.html', context)