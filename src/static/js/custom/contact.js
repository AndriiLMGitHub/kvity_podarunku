(function () {
    'use strict';

    function initAjaxContactForm() {
        const form = document.getElementById('contact-form');
        if (!form) return;

        if (form.dataset.ajaxBound === 'true') return;
        form.dataset.ajaxBound = 'true';

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (e.stopImmediatePropagation) {
                e.stopImmediatePropagation();
            }

            const formData = new FormData(form);
            formData.append('is_ajax', 'true');

            // Отримання CSRF-токена
            let csrftoken = '';
            const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                csrftoken = csrfInput.value;
            } else {
                const match = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
                if (match) csrftoken = match[2];
            }

            // Пошук або створення контейнера для сповіщень
            let alertBox = document.getElementById('form-alert-box');
            if (!alertBox) {
                alertBox = document.createElement('div');
                alertBox.id = 'form-alert-box';
                alertBox.style.cssText = 'margin-top: 20px;';
                form.prepend(alertBox);
            }

            // 1. КРЕАТИВНИЙ ТА СТИЛЬНИЙ ЛОАДЕР (замість alert-info)
            alertBox.innerHTML = `
                <div class="d-flex align-items-center p-3 mb-3 bg-white rounded-0 shadow-sm" style="border-left: 4px solid #80b435; border: 1px solid #eaeaea;">
                    <div class="spinner-border spinner-border-sm text-success me-3" role="status" style="width: 1.5rem; height: 1.5rem; border-width: 0.2em;"></div>
                    <div>
                        <h6 class="mb-0 fw-bold text-dark" style="font-size: 15px;">Обробка запиту...</h6>
                        <small class="text-muted">Будь ласка, зачекайте хвилину, ми надсилаємо ваше повідомлення.</small>
                    </div>
                </div>
            `;

            fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
                .then(async response => {
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.includes("application/json")) {
                        return response.json().then(data => ({ ok: response.ok, data }));
                    } else {
                        throw new Error("Сервер повернув не JSON-відповідь.");
                    }
                })
                .then(({ ok, data }) => {
                    if (ok && data.status === 'success') {
                        // 2. КРАСИВИЙ УСПІШНИЙ АЛЕРТ З ІКОНКОЮ
                        alertBox.innerHTML = `
                        <div class="alert alert-success d-flex align-items-center rounded-0 shadow-sm border-0 p-3 mb-3" role="alert" style="background-color: #f1f8e9; color: #33691e; border-left: 4px solid #7cb342 !important;">
                            <i class="fas fa-check-circle fa-2x me-3 text-success" style="color: #7cb342 !important;"></i>
                            <div>
                                <h6 class="alert-heading mb-1 fw-bold" style="font-size: 16px;">Успішно відправлено!</h6>
                                <p class="mb-0" style="font-size: 14px;">${data.message}</p>
                            </div>
                        </div>
                    `;
                        form.reset();

                        // Оновлення nice-select, якщо використовується
                        if (window.jQuery && jQuery('select.nice-select').length) {
                            jQuery('select.nice-select').niceSelect('update');
                        }
                    } else {
                        // 3. СТИЛЬНИЙ АЛЕРТ ПОМИЛКИ ВАЛІДАЦІЇ З ІКОНКОЮ
                        alertBox.innerHTML = `
                        <div class="alert alert-warning d-flex align-items-center shadow-sm rounded-0 border-0 p-3 mb-3" role="alert" style="background-color: #fff8e1; color: #ff8f00; border-left: 4px solid #ffb300 !important;">
                            <i class="fas fa-exclamation-triangle fa-2x me-3" style="color: #ffb300 !important;"></i>
                            <div>
                                <h6 class="alert-heading mb-1 fw-bold" style="font-size: 16px; color: #ff8f00;">Зверніть увагу</h6>
                                <p class="mb-0" style="font-size: 14px; color: #5d4037;">${data.message || 'Перевірте правильність заповнених полів.'}</p>
                            </div>
                        </div>
                    `;
                    }
                })
                .catch(error => {
                    // 4. СТИЛЬНИЙ АЛЕРТ СИСТЕМНОЇ ПОМИЛКИ З ІКОНКОЮ
                    alertBox.innerHTML = `
                    <div class="alert alert-danger d-flex align-items-center rounded-0 shadow-sm border-0 p-3 mb-3" role="alert" style="background-color: #ffebee; color: #c62828; border-left: 4px solid #e53935 !important;">
                        <i class="fas fa-times-circle fa-2x me-3 text-danger" style="color: #e53935 !important;"></i>
                        <div>
                            <h6 class="alert-heading mb-1 fw-bold" style="font-size: 16px;">Помилка сервера</h6>
                            <p class="mb-0" style="font-size: 14px;">Сталася непередбачена помилка. Спробуйте пізніше або зателефонуйте нам напряму.</p>
                        </div>
                    </div>
                `;
                    console.error('Fetch error:', error);
                });

            return false;
        }, true);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAjaxContactForm);
    } else {
        initAjaxContactForm();
    }
})();