from django.shortcuts import render
from .models import Product

def get_all_products(request):
    products = Product.objects.all()
    context={
        'products': products,
    }
    return render(request, 'index.html', context)
