from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_products, name='product_list'),
    path('category/<slug:category_slug>/',views.get_products,name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]