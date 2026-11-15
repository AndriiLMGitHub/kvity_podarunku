import logging

from django.utils import timezone
from django.shortcuts import render
from django import http

from modules.blog.models import BlogPost
from modules.portfolio.models import PortfolioWork
from modules.reviews.models import Testimonial
from modules.shop.models import Category


logger = logging.getLogger(__name__)

# Main page view
def home_view(request: http.HttpRequest) -> http.HttpResponse:
    """
    Відображає головну сторінку сайту.
    """
    logger.info("Homepage requested")
    categories = Category.objects.filter(is_active=True, parent=None).order_by('sort_order')
    portfolio_works = PortfolioWork.objects.filter(is_published=True).order_by('order')[:3]
    posts = BlogPost.objects.filter(
        is_published=True,
        published_at__lte=timezone.now(),
    ).order_by('-published_at')[:3]
    testimonials = Testimonial.objects.filter(is_published=True).order_by('order')
    context = {
        'categories': categories,
        'portfolio_works': portfolio_works,
        'latest_posts': posts,
        'testimonials': testimonials,
    }
    return render(request, 'pages/index.html', context)


# Error handlers
def custom_404_view(request: http.HttpRequest, exception=None) -> http.HttpResponseNotFound:
    logger.warning(f"404 Not Found: {request.path}")
    return render(request, 'errors/404.html', status=404)

def custom_403_view(request: http.HttpRequest, exception=None) -> http.HttpResponseForbidden:
    logger.warning(f"403 Forbidden: {request.user} спробував отримати доступ до {request.path}")
    return render(request, 'errors/403.html', status=403)

def custom_400_view(request: http.HttpRequest, exception=None) -> http.HttpResponseBadRequest:
    logger.warning(f"400 Bad Request: {request.path}")
    return render(request, 'errors/400.html', status=400)

def custom_500_view(request: http.HttpRequest) -> http.HttpResponseServerError:
    logger.error(f"500 Server Error на шляху {request.path}")
    return render(request, 'errors/500.html', status=500)