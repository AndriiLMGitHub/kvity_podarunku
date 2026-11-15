import logging

from django.http import JsonResponse
from django.shortcuts import render

from django.shortcuts import render
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .forms import ContactMessageForm


logger = logging.getLogger(__name__)


def contact_view(request):
    # Якщо це GET-запит (просто відкрили сторінку) — віддаємо HTML
    if request.method == 'GET':
        return render(request, 'contact/contact.html')

    # Якщо це POST-запит (відпрацював твій JavaScript) — працюємо як API
    form = ContactMessageForm(request.POST)

    if not form.is_valid():
        # Передаємо form.errors на фронтенд, щоб твій JS міг підсвітити червоним конкретні поля
        return JsonResponse({
            'status': 'error',
            'message': _("Перевірте правильність введених даних."),
            'errors': form.errors 
        }, status=400)

    # 1. Збереження в БД
    contact_msg = form.save()

    # 2. Формування листа
    email_subject = f"Нове звернення з сайту від {contact_msg.name}"

    # Рендеримо наш гарний HTML-шаблон, передаючи туди об'єкт з бази
    html_message = render_to_string('emails/contact_notification.html', {'contact_msg': contact_msg})

    # Генеруємо чистий текст (без HTML-тегів) для старих поштових клієнтів (Fall-back)
    plain_message = strip_tags(html_message)
    
    # 3. Відправка Email
    try:
        send_mail(
            subject=email_subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[getattr(settings, 'ADMIN_EMAIL', 'kvity1331@gmail.com')],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Контактна форма: email успішно відправлено ({contact_msg.email}).")
    except Exception as e:
        logger.error(f"Контактна форма: збій SMTP для {contact_msg.email}: {e}", exc_info=True)
        # Лід у базі є, тому не повертаємо статус 500 для клієнта. 

    # 4. Відповідь для твого JavaScript
    return JsonResponse({
        'status': 'success',
        'message': _("Ваше повідомлення успішно відправлено! Ми зв'яжемося з вами найближчим часом.")
    })
    