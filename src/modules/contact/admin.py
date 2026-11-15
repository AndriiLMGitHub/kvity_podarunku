from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # UI/UX: Що бачимо в загальній таблиці
    list_display = ('name', 'phone', 'email', 'service_type', 'created_at', 'is_processed')
    
    # UI/UX: Дозволяємо менеджеру перемикати статус прямо з таблиці, не заходячи всередину
    list_editable = ('is_processed',)
    
    # UI/UX: Швидкі фільтри в правій панелі
    list_filter = ('is_processed', 'service_type')
    
    # Пошук по всіх ключових текстових полях
    search_fields = ('name', 'email', 'phone', 'message')
    
    # UI/UX: Навігація по датах звернень над таблицею
    date_hierarchy = 'created_at'
    
    # Архітектурне правило: Дані клієнта ЗАБОРОНЕНО редагувати. Вони лише для читання.
    readonly_fields = ('name', 'email', 'phone', 'service_type', 'message', 'created_at')
    
    # UI/UX: Логічне групування полів на сторінці детального перегляду
    fieldsets = (
        (_('Статус заявки'), {
            'fields': ('is_processed', 'created_at'),
            'classes': ('wide',),
        }),
        (_('Контактні дані'), {
            'fields': ('name', 'email', 'phone'),
        }),
        (_('Суть звернення'), {
            'fields': ('service_type', 'message'),
        }),
    )

    # Масові дії для роботи з десятками лідів одночасно
    actions = ['mark_as_processed', 'mark_as_unprocessed']

    @admin.action(description=_('Позначити вибрані як оброблені'))
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, _(f"{updated} заявок успішно позначено як оброблені."))

    @admin.action(description=_('Позначити вибрані як НЕ оброблені'))
    def mark_as_unprocessed(self, request, queryset):
        updated = queryset.update(is_processed=False)
        self.message_user(request, _(f"{updated} заявок повернуто в статус необроблених."))

    # Архітектурне правило: Заборонити кнопку "Додати" в адмінці.
    # Заявки мають надходити ТІЛЬКИ через форму на сайті.
    def has_add_permission(self, request):
        return False