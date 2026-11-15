import logging

from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404

from .utils import paginate_queryset
from .models import Product, Category, ProductImage

logger = logging.getLogger(__name__)


def get_products(request, category_slug=None):
    # 1. Запитуємо оптимізовану базу товарів
    products_qs = Product.objects.active_with_related()
    category = None

    # 2. Звужуємо вибірку за категорією
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products_qs = products_qs.in_category(category)

    # 3. Застосовуємо сортування
    sort_param = request.GET.get('sort', 'default')
    products_qs = products_qs.sort_by_param(sort_param)

    # 4. Пагінуємо результати
    page_obj, paginator = paginate_queryset(request, products_qs, per_page=12)

    context = {
        'category': category,
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    }

    return render(request, 'shop/shop.html', context)



def product_detail(request, slug):
    # У галереї спочатку головне фото, потім інші.
    # to_attr не створює додаткових запитів до БД при виводі фото.
    photos = Prefetch(
        "images",
        queryset=ProductImage.objects.order_by("-is_main", "created_at", "pk"),
        to_attr="gallery_images",
    )

    product = get_object_or_404(
        Product.objects.active()
        .filter(category__is_active=True)
        .select_related("category")
        .prefetch_related(photos),
        slug=slug,
    )

    related_products = (
        Product.objects.active()
        .filter(category=product.category, category__is_active=True)
        .exclude(pk=product.pk)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("-is_main", "created_at", "pk"),
                to_attr="gallery_images",
            )
        )
        .order_by("-created_at")[:4]
    )

    return render(
        request,
        "shop/product_detail.html",  # Якщо файл лежить у templates/shop/
        {
            "product": product,
            "gallery_images": product.gallery_images,
            "related_products": related_products,
            "add_to_cart_url": None,  # Вкажи реальний POST URL, коли буде реалізований кошик.
        },
    )