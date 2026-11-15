from django.utils import timezone
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Q, Index, Prefetch
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from decimal import Decimal
from django.db import models, transaction
from django.db.models import Q, Index
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class ProductQuerySet(models.QuerySet):
    def active(self):
        """Повертає лише активні товари."""
        return self.filter(is_active=True)

    def with_related(self):
        """Підтягує категорію та попередньо завантажує головне фото (боротьба з N+1)."""
        from .models import ProductImage  # Локальний імпорт для уникнення circular import
        
        main_image_prefetch = Prefetch(
            'images',
            queryset=ProductImage.objects.filter(is_main=True),
            to_attr='prefetched_main_images' 
        )
        return self.select_related('category').prefetch_related(main_image_prefetch)

    def active_with_related(self):
        """Комбінований метод для каталогів: активні товари з оптимізованими зв'язками."""
        return self.active().with_related()

    def in_category(self, category):
        """Фільтрує товари за категорією та її активними підкатегоріями."""
        category_ids = [category.id] + list(
            category.children.filter(is_active=True).values_list('id', flat=True)
        )
        return self.filter(category_id__in=category_ids)

    def sort_by_param(self, sort_param):
        """Мапінг GET-параметра на SQL сортування."""
        sort_mapping = {
            'name_asc': 'name',
            'old': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'default': '-created_at',
        }
        # Безпечно повертаємо '-created_at' при некоректному чи відсутньому параметрі
        order_field = sort_mapping.get(sort_param, '-created_at')
        return self.order_by(order_field)
    
    

class Category(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name=_('Назва категорії')
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        db_index=True,
        verbose_name=_('URL-слаг'),
        help_text=_('Частина посилання. Заповнюється автоматично.')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Батьківська категорія')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Порядок сортування'),
        help_text=_('Визначає порядок виводу (0 - найвище)')
    )

    class Meta:
        verbose_name = _('категорія') 
        verbose_name_plural = _('Категорії')
        ordering = ['sort_order', 'name']
        indexes = [
            Index(fields=['parent', 'is_active']),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Категорія')
    )
    sku = models.CharField(
        max_length=64, 
        unique=True, 
        db_index=True,
        verbose_name=_('Артикул (SKU)')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Назва товару')
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True,
        verbose_name=_('URL-слаг')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Опис')
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Ціна')
    )
    old_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Стара ціна')
    )
    stock = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name=_('Залишок на складі')
    )
    badge = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Бейджик'),
        help_text=_('Наприклад: "Новинка", "Хіт продажів", "-25%" тощо. Може бути порожнім.'),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активний')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Створено')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Оновлено')
    )
    
    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _('товар')
        verbose_name_plural = _('Товари')
        ordering = ['-created_at']
        indexes = [
            Index(fields=['is_active', 'category', '-created_at']),
            Index(fields=['price']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=Decimal('0.00')),
                name='product_price_non_negative'
            ),
            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name='product_stock_non_negative'
            )
        ]

    def __str__(self):
        # Виправлено синтаксичну помилку з розірваним рядком
        return f"{self.sku} - {self.name}"



class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Товар')
    )
    image = models.ImageField(
        upload_to='products/%Y/%m/%d/',
        verbose_name=_('Зображення')
    )
    is_main = models.BooleanField(
        default=True,
        verbose_name=_('Головне фото')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Завантажено')
    )
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_main:
                Product.objects.select_for_update().get(
                    pk=self.product_id
                )

                ProductImage.objects.filter(
                    product_id=self.product_id,
                    is_main=True
                ).exclude(pk=self.pk).update(
                    is_main=False
                )

            super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('зображення')
        verbose_name_plural = _('Галерея товару')
        indexes = [
            Index(fields=['product', 'is_main']),
        ]
        
    