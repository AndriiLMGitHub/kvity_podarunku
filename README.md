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

Цей проєкт локально використовує MySQL. Для безкоштовного тестового розгортання можна використати Render PostgreSQL: якщо задано `DATABASE_URL`, Django під’єднується до PostgreSQL; без нього локальний Docker Compose продовжує використовувати MySQL. Render безкоштовно не надає MySQL із постійним диском.

Render збирає застосунок із Git, а не з локального `.env`. Перед деплоєм додайте до потрібної гілки всі файли застосунку, зокрема `src/static/`, і відправте її в репозиторій. Не додавайте `.env` або `backups/`.

### 1. Створіть базу даних

#### Безкоштовно: Render PostgreSQL (для демо)

1. У Render виберіть **New → Postgres**, план **Free**, регіон для бази. Скопіюйте **Internal Database URL**.
2. Застосунок має використовувати цю URL у змінній `DATABASE_URL` (див. крок 3).
3. Нова база порожня: міграції створять таблиці, але дані з локальної MySQL автоматично не перенесуться.

Безкоштовна база PostgreSQL Render має обмежений термін дії — **30 днів**. Це варіант для демо або тестування, а не для постійного зберігання даних.

#### MySQL (платний варіант)

1. Створіть власну копію офіційного [Render MySQL template](https://github.com/render-examples/mysql), як описано в [інструкції Render](https://render.com/docs/deploy-mysql).
2. Створіть **Private Service** із **Language: Docker** у тому самому регіоні, що й вебсервіс. Задайте в MySQL-сервісі `MYSQL_DATABASE`, `MYSQL_USER` (не `root`), `MYSQL_PASSWORD` і окремий `MYSQL_ROOT_PASSWORD`.
3. Додайте постійний диск із **Mount Path** `/var/lib/mysql` та виберіть платний план. Дочекайтеся статусу **Live** і скопіюйте внутрішню адресу MySQL, наприклад `mysql-foo:3306`. Для `DB_HOST` потрібна лише частина `mysql-foo`.

### 2. Створіть вебсервіс

1. Виберіть **New → Web Service**, під’єднайте репозиторій сайту та потрібну гілку.
2. Виберіть **Language: Docker**, Dockerfile `./Dockerfile` і контекст `.`. Обидва сервіси мають бути в одному регіоні. Не запускайте на Render `docker-compose.yml` або локальний Nginx: Render надає власний HTTP/HTTPS proxy.
3. Залиште **Docker Command** порожньою, щоб використати команду з Dockerfile. Вона спочатку застосовує міграції, збирає static-файли, а потім запускає Gunicorn на порту `PORT`, який задає Render. Якщо раніше в Render було збережено власну **Docker Command**, очистьте її — інакше вона перекриє команду з Dockerfile. Django також налаштований розпізнавати HTTPS за заголовком `X-Forwarded-Proto` від проксі Render.

4. У **Environment** вебсервісу додайте спільні змінні:

   | Змінна | Значення |
   | --- | --- |
   | `DEBUG` | `False` |
   | `SECRET_KEY` | Створіть секретне значення через **Generate** |
   | `ALLOWED_HOSTS` | Домен сервісу, наприклад `flower-shop.onrender.com`; кілька доменів — через кому без пробілів |

   Додайте **один** набір змінних для обраної бази:

   - Для безкоштовного PostgreSQL: `DATABASE_URL` — **Internal Database URL** із кроку 1. Не додавайте її до репозиторію.
   - Для MySQL: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` (внутрішній hostname без порту) та `DB_PORT=3306`. `DB_USER` і пароль мають відповідати `MYSQL_USER` та `MYSQL_PASSWORD` у MySQL-сервісі.

   `DATABASE_URL` має пріоритет над MySQL-змінними. `PORT` задається Render автоматично. Якщо використовуються медіафайли або надсилання листів, додайте потрібні `CLOUDINARY_*` і `EMAIL_*`.

5. Створіть Web Service, дочекайтеся успішного деплою та відкрийте його адресу `*.onrender.com`. HTTPS для Web Service надає Render.

### Помилка `relation "shop_category" does not exist`

Це означає, що застосунок під’єднався до PostgreSQL, у якому ще не застосована міграція `shop.0001_initial`. Переконайтеся, що в Render не задано власну **Docker Command**, яка перекриває команду з Dockerfile, а `DATABASE_URL` вебсервісу вказує на потрібну базу. У `shop.0001_initial` є створення таблиці категорій.

Якщо міграцію потрібно застосувати вручну на Free-плані, запустіть із кореня проєкту локальний Docker-контейнер, під’єднавши його до **External Database URL** із Render:

```sh
printf 'External Database URL (input hidden): '
read -r -s DATABASE_URL
printf '\n'
export DATABASE_URL
docker compose run --rm --build --no-deps -e DATABASE_URL web python manage.py showmigrations shop
docker compose run --rm --no-deps -e DATABASE_URL web python manage.py migrate --noinput
unset DATABASE_URL
```

У `showmigrations` переконайтеся, що `shop.0001_initial` позначена `[X]`. Якщо після міграції помилка лишилася, звірте, що `DATABASE_URL` у вебсервісі та External Database URL належать саме тій самій базі. Не використовуйте `--fake` і не видаляйте базу.

### Створення адміністратора на Free-плані

Render Free не надає Shell для вебсервісу. Для створення адміністратора можна запустити management-команду локально з Docker, під’єднавшись до **External Database URL** PostgreSQL:

```sh
printf 'External Database URL (input hidden): '
read -r -s DATABASE_URL
printf '\n'
export DATABASE_URL
docker compose run --rm --build --no-deps -e DATABASE_URL web python manage.py createsuperuser
unset DATABASE_URL
```

Коли команда попросить, вставте External Database URL із Render і натисніть Enter. Цей URL містить пароль — не публікуйте його. Для зовнішнього підключення Render вимагає TLS; використовуйте URL, скопійовану з Dashboard.

### Обмеження безкоштовного плану

- Free Web Service вимикається після 15 хвилин без запитів; перше відкриття після простою може зайняти близько хвилини.
- Файлова система Free Web Service тимчасова. Для медіафайлів налаштуйте Cloudinary; не зберігайте їх лише на диску вебконтейнера.
- Free PostgreSQL закінчується через 30 днів. Робіть окремі експорти потрібних даних.
- Render Free блокує вихідні SMTP-з’єднання на портах `25`, `465` і `587`. Для листів потрібен email API через HTTPS або платний план.
- Для постійного сайту з MySQL використовуйте платний MySQL-сервіс із диском; диск MySQL має бути `/var/lib/mysql`. Render не радить відновлювати власну MySQL-базу зі snapshot диска — використовуйте `mysqldump`.

Офіційні інструкції: [Docker на Render](https://render.com/docs/docker), [Django](https://render.com/docs/deploy-django), [безкоштовний план](https://render.com/docs/free), [Render PostgreSQL](https://render.com/docs/postgresql-creating-connecting), [Render MySQL](https://render.com/docs/deploy-mysql).
