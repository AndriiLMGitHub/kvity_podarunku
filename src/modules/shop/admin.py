from django.contrib import admin
from django.utils.html import mark_safe
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group

from .models import Category, Product, ProductImage

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass



class ProductImageFormSet(BaseInlineFormSet):
    """
    Гарантує, що контент-менеджер не зможе зберегти товар
    із двома головними фотографіями або взагалі без них.
    """
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        main_images_count = 0
        valid_forms_exist = False

        for form in self.forms:
            if not form.cleaned_data or (self.can_delete and self._should_delete_form(form)):
                continue
                
            valid_forms_exist = True
            if form.cleaned_data.get('is_main'):
                main_images_count += 1

        if valid_forms_exist:
            if main_images_count > 1:
                raise ValidationError("Помилка: Товар може мати строго ОДНЕ головне фото.")
            if main_images_count == 0:
                raise ValidationError("Помилка: Необхідно обрати хоча б одне головне фото (is_main).")



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageFormSet
    extra = 0  # Ніяких порожніх рядків за замовчуванням (мінімалізм)
    min_num = 1 # Вимагаємо мінімум одне фото
    
    # Визначаємо порядок полів, додаючи кастомне прев'ю
    fields = ('image_preview', 'image', 'is_main')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        """Рендерить мініатюру прямо в рядку інлайну."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height: 60px; border-radius: 4px; object-fit: cover;" />')
        return "Немає фото"
    image_preview.short_description = "Прев'ю"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    # autocomplete_fields критично необхідний для parent, 
    # щоб при 100+ категоріях адмінка не гальмувала від випадаючого списку
    autocomplete_fields = ('parent',) 


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Оптимізація запитів: без select_related на category буде N+1 проблема
    list_select_related = ('category',) 
    
    list_display = (
        'get_main_image', 'sku', 'name', 'category', 
        'price', 'stock', 'is_active'
    )
    # Швидке редагування запасів та статусу прямо зі списку. 
    # Ціну не редагуємо тут з міркувань фінансової безпеки (випадковий клік).
    list_editable = ('stock', 'is_active')
    
    list_filter = ('is_active', 'category')
    search_fields = ('sku', 'name')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Логічне групування (Fieldsets) — основа мінімалізму та UX
    fieldsets = (
        ('Основна інформація', {
            'fields': ('category', 'name', 'slug', 'badge','description')
        }),
        ('Комерція та Склад', {
            'fields': ('sku', 'price', 'old_price', 'stock', 'is_active'),
            'classes': ('collapse',) # Згортаємо, якщо менеджеру треба лише змінити опис
        }),
        ('Системна інформація', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline]

    def get_main_image(self, obj):
        """
        Витягує головне фото для list_display. 
        Увага: це створює додаткові запити. Дивись зауваження нижче.
        """
        main_img = obj.images.filter(is_main=True).first()
        if main_img and main_img.image:
            return mark_safe(f'<img src="{main_img.image.url}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;" />')
        return "—"
    get_main_image.short_description = 'Фото'

    def get_queryset(self, request):
        """
        Перевизначаємо QuerySet для Prefetching зображень, 
        щоб метод get_main_image не поклав базу (захист від N+1).
        """
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            models.Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_main=True),
                to_attr='main_image_cache'
            )
        )

    def get_main_image(self, obj):
        """Оптимізована версія рендерингу мініатюри з кешу Prefetch"""
        if hasattr(obj, 'main_image_cache') and obj.main_image_cache:
            main_img = obj.main_image_cache[0]
            if main_img.image:
                 return mark_safe(f'<img src="{main_img.image.url}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;" />')
        return "—"
    get_main_image.short_description = 'Фото'
    
    