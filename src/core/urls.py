from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.home_view, name="index"),
    
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
]