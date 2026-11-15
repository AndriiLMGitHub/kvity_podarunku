# Квіти та подарунки

Django-застосунок для магазину квітів і подарунків. У проєкті є каталог товарів, блог, портфоліо, відгуки та контактна форма.

## Стек

- Django і Gunicorn — вебзастосунок.
- MySQL 8.4 — база даних.
- Nginx — reverse proxy та роздача static-файлів.
- Окремий сервіс Compose — автоматичне резервне копіювання бази.

## Що потрібно

- Docker Desktop або Docker Engine із Docker Compose v2.
- Вільний порт `80` (або інший порт, заданий через `HTTP_PORT`).

## Перший запуск

1. Переконайтеся, що Docker запущений.
2. Якщо файлу `.env` ще немає, створіть його з шаблону:

   ```sh
   if [ ! -f .env ]; then cp .env.example .env; fi
   ```

3. Відредагуйте `.env`: встановіть надійні значення для `SECRET_KEY`, `DB_PASSWORD` і `MYSQL_ROOT_PASSWORD`. Згенерувати ключ можна командою:

   ```sh
   python3 -c 'import secrets; print(secrets.token_urlsafe(50))'
   ```

   Вставте його в `.env` у одинарних лапках, наприклад `SECRET_KEY='згенерований-ключ'`.

4. Перевірте налаштування бази:

   ```dotenv
   DB_NAME=flower_site
   DB_USER=flower_site
   DB_PASSWORD=встановіть-надійний-пароль
   DB_HOST=db
   DB_PORT=3306
   MYSQL_ROOT_PASSWORD=встановіть-інший-надійний-пароль
   ```

   `DB_USER` має бути окремим користувачем застосунку, не `root`. Значення `DB_HOST=db` потрібне для підключення між контейнерами Compose.

5. Зберіть образ і запустіть сервіси:

   ```sh
   docker compose up --build -d
   ```

6. Відкрийте сайт: <http://localhost>. Якщо змінили `HTTP_PORT`, використовуйте відповідний порт, наприклад <http://localhost:8080>.

Під час запуску `web` дочекається готовності MySQL, виконає міграції та збере static-файли перед стартом Gunicorn. Nginx почне приймати запити після того, як вебзастосунок стане готовим.

## Налаштування `.env`

Файл `.env.example` містить повний перелік змінних. Основні:

| Змінна | Призначення |
| --- | --- |
| `SECRET_KEY` | Секретний ключ Django. Не додавайте справжнє значення до Git. |
| `DEBUG` | Режим Django: `False` для звичайного запуску, `True` — лише для локальної розробки. |
| `ALLOWED_HOSTS` | Дозволені домени, через кому без пробілів. Для публічного сайту додайте його домен. |
| `HTTP_PORT` | Порт на хості, опублікований Nginx; за замовчуванням `80`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Назва бази та облікові дані користувача застосунку. |
| `DB_HOST`, `DB_PORT` | Адреса й порт MySQL у мережі Compose; типові значення — `db` і `3306`. |
| `MYSQL_ROOT_PASSWORD` | Пароль адміністратора MySQL; має відрізнятися від `DB_PASSWORD`. |
| `BACKUP_INTERVAL_SECONDS` | Інтервал резервного копіювання в секундах; типовий — `86400` (24 години). |
| `BACKUP_RETENTION_DAYS` | Кількість днів зберігання дампів; типовий — `14`. |

Для завантаження та зберігання медіафайлів заповніть `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` і `CLOUDINARY_API_SECRET`. Для надсилання листів налаштуйте змінні `EMAIL_*`.

Не публікуйте `.env` і не зберігайте в репозиторії реальні паролі чи ключі.

## Корисні команди

```sh
# Стан контейнерів
docker compose ps

# Перегляд логів
docker compose logs -f web nginx db

# Логи резервного копіювання
docker compose logs -f db-backup

# Створити адміністратора Django
docker compose exec web python manage.py createsuperuser

# Запустити тести Django
docker compose exec web python manage.py test

# Зупинити сервіси
docker compose down
```

`docker compose down` зупиняє та видаляє контейнери, але зберігає базу у volume `mysql_data` і резервні копії в `./backups`. **Не додавайте `-v`**, якщо не хочете видалити дані MySQL у volume.

MySQL налаштовує початкову базу та користувача лише під час першої ініціалізації volume. Якщо змінити `DB_NAME`, `DB_USER` або паролі після запуску, значення в уже створеній базі автоматично не зміняться. Не видаляйте volume з даними заради застосування нових значень — змініть облікові дані в MySQL або відновіть базу з резервної копії.

Після змін у коді перебудуйте образ:

```sh
docker compose up --build -d
```

## Резервні копії та відновлення

Сервіс `db-backup` створює перший стиснений дамп після готовності MySQL, а потім повторює копіювання з інтервалом `BACKUP_INTERVAL_SECONDS`. Файли мають формат `.sql.gz` і зберігаються в `./backups`; старі дампи видаляються відповідно до `BACKUP_RETENTION_DAYS`.

Перевірити наявні копії:

```sh
ls -lh ./backups
```

Щоб відновити дамп, замініть шлях на потрібний файл:

```sh
gzip -dc ./backups/flower_site_20261115T120000Z.sql.gz \
  | docker compose exec -T db sh -c \
    'MYSQL_PWD="$MYSQL_PASSWORD" mysql --host=127.0.0.1 --user="$MYSQL_USER" "$MYSQL_DATABASE"'
```

Відновлення замінює таблиці та дані з дампа. Перед ним збережіть поточний стан бази. Копії в `./backups` знаходяться на тому ж хості, що й застосунок; для захисту від втрати сервера регулярно копіюйте їх у зашифроване зовнішнє або віддалене сховище.

## Розгортання на Render

Цей проєкт використовує MySQL. Render надає керований PostgreSQL, але для збереження поточної MySQL-конфігурації використовуйте окремий приватний MySQL-сервіс із постійним диском. Такий MySQL-сервіс і диск потребують платного плану. Якщо потрібне безкоштовне кероване сховище Render, спершу потрібно перенести проєкт із MySQL на PostgreSQL.

Render збирає застосунок із Git-репозиторію, а не з локального `.env` або `docker-compose.yml`. Перед деплоєм переконайтеся, що потрібний код і папка `src/static/` додані до Git та відправлені в обрану гілку. `src/static/` містить вихідні CSS, JS і зображення; не додавайте до Git `.env` або `backups/`.

### 1. Створіть MySQL-сервіс

1. У Render створіть власну копію офіційного [Render MySQL template](https://github.com/render-examples/mysql) або скористайтеся інструкцією [Deploy MySQL](https://render.com/docs/deploy-mysql).
2. У Dashboard виберіть **New → Private Service**, під’єднайте копію репозиторію, встановіть **Language: Docker** і виберіть ту саму гілку, що й для вебзастосунку.
3. Виберіть регіон і платний план. У змінних середовища MySQL-сервісу задайте:

   | Змінна | Значення |
   | --- | --- |
   | `MYSQL_DATABASE` | Назва бази, наприклад `flower_site` |
   | `MYSQL_USER` | Окремий користувач застосунку, наприклад `flower_site` (не `root`) |
   | `MYSQL_PASSWORD` | Надійний пароль цього користувача |
   | `MYSQL_ROOT_PASSWORD` | Окремий надійний пароль `root` |

4. Додайте диск у налаштуваннях сервісу: **Mount Path** — `/var/lib/mysql`; виберіть розмір, наприклад 10 GB. Це обов’язковий шлях для даних MySQL.
5. Створіть сервіс і дочекайтеся статусу **Live**. Скопіюйте його внутрішню адресу з Dashboard, наприклад `mysql-foo:3306`. Для `DB_HOST` потрібна лише частина до двокрапки (`mysql-foo`).

### 2. Створіть вебсервіс

1. У Render виберіть **New → Web Service** і під’єднайте репозиторій цього сайту.
2. Виберіть гілку з актуальним кодом, регіон та **Language: Docker**. Вкажіть Dockerfile `./Dockerfile` і контекст `.`. Не запускайте на Render локальний `docker-compose.yml` чи окремий Nginx: Render надає зовнішній HTTP/HTTPS proxy.
3. У полі **Docker Command** (розділ **Advanced**) задайте команду запуску:

   ```sh
   /bin/sh -c 'python manage.py migrate --noinput && python manage.py collectstatic --noinput --upload-unhashed-files && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --access-logfile - --error-logfile -'
   ```

   Render передає порт через `PORT`. Команда запускає міграції, збирає static-файли та прив’язує Gunicorn до потрібного Render порту.

4. У **Environment** вебсервісу додайте:

   | Змінна | Значення |
   | --- | --- |
   | `DEBUG` | `False` |
   | `SECRET_KEY` | Створіть секретне значення через **Generate** або згенеруйте окремо |
   | `ALLOWED_HOSTS` | Домен сервісу, наприклад `flower-shop.onrender.com`; кілька доменів — через кому без пробілів |
   | `DB_NAME` | Те саме значення, що й `MYSQL_DATABASE` у MySQL-сервісі |
   | `DB_USER` | Те саме значення, що й `MYSQL_USER` |
   | `DB_PASSWORD` | Те саме значення, що й `MYSQL_PASSWORD` |
   | `DB_HOST` | Внутрішній hostname MySQL-сервісу без порту |
   | `DB_PORT` | `3306` |

   `MYSQL_ROOT_PASSWORD` вебсервісу не потрібен. `PORT` задає Render автоматично. Якщо сайт використовує Cloudinary чи SMTP, додайте відповідні змінні `CLOUDINARY_*` та `EMAIL_*`.

5. Створіть Web Service та перевірте **Events** і **Logs**. Після успішного деплою відкрийте адресу `*.onrender.com`. У Render Shell можна створити адміністратора:

   ```sh
   python manage.py createsuperuser
   ```

### Важливо для Render

- WhiteNoise роздає зібрані static-файли; його middleware розміщений одразу після `SecurityMiddleware`. Якщо в Render змінювали налаштування, переконайтеся, що використовується останній коміт.
- Переконайтеся, що в Git є всі потрібні файли проєкту, особливо `src/static/`; Render не побачить локальні або проігноровані Git файли.
- Новий MySQL-сервіс починається з порожньої бази. Якщо у локальній базі є потрібні дані, експортуйте їх і перенесіть до першого запуску сайту на Render.
- Локальний сервіс `db-backup` із Compose на Render не запускається. Налаштуйте окремі регулярні `mysqldump`-копії у віддалене сховище. Для власного MySQL Render не рекомендує відновлювати базу зі snapshot диска.
- Render завершує TLS для Web Service автоматично. Для власного домену додайте його в налаштування доменів Render і в `ALLOWED_HOSTS`.

Документація Render: [Docker](https://render.com/docs/docker), [MySQL](https://render.com/docs/deploy-mysql), [Web Services і порт `PORT`](https://render.com/docs/web-services), [диски](https://render.com/docs/disks), [змінні середовища](https://render.com/docs/configure-environment-variables).
