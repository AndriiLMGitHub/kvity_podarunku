from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('id', 'avatar_preview', 'author_name', 'author_role', 'is_published', 'order', 'created_at')
    list_display_links = ('id', 'author_name')
    list_editable = ('is_published', 'order')
    search_fields = ('author_name', 'text')
    list_filter = ('is_published', 'created_at')
    readonly_fields = ('created_at',)

    @admin.display(description=_("Фото"))
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height: 50px; border-radius: 50%;" alt="{}" />',
                obj.avatar.url, 
                obj.author_name
            )
        return "-"
