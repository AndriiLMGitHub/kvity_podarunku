from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import PortfolioWork

@admin.register(PortfolioWork)
class PortfolioWorkAdmin(admin.ModelAdmin):
    list_display = ('id', 'image_preview', 'title', 'is_published', 'order', 'created_at')
    list_display_links = ('id', 'title')
    list_editable = ('is_published', 'order')
    search_fields = ('title',)
    list_filter = ('is_published', 'created_at')
    readonly_fields = ('created_at',)

    @admin.display(description=_("Thumbnail"))
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 4px;" alt="{}" />',
                obj.image.url, 
                obj.title
            )
        return "-"