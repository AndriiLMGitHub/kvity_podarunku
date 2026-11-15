from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('contact/', include('modules.contact.urls')),
    path('blog/', include('modules.blog.urls')),
    path('shop/', include('modules.shop.urls')),
    
    
)

handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'
handler403 = 'core.views.custom_403_view'
handler400 = 'core.views.custom_400_view'
