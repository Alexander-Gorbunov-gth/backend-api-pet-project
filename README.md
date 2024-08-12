Foodgram реализован для публикации рецептов. Авторизованные пользователи
могут подписываться на понравившихся авторов, добавлять рецепты в избранное,
в покупки, скачать список покупок ингредиентов для добавленных в покупки
рецептов.

## Стэк:

- Python 3.11
- Django 3.2.3
- Django REST framework 3.12.4
- Nginx
- Docker
- Postgres

## Для работы с удаленным сервером (на ubuntu):
* Склонировать репозиторий на локальную машину:
* Выполните вход на свой удаленный сервер
* Установите docker на сервер:
* Установите docker-compose на сервер:
* Скопируйте файлы docker-compose.production.yml на сервер
* Cоздайте .env файл и впишите:
    ```
    POSTGRES_USER=
    POSTGRES_PASSWORD=
    POSTGRES_DB=
    DB_HOST=
    DB_PORT=5432
    SECRET_KEY=
    DEBUG=True
    ```

* На сервере соберите docker-compose:
```
sudo docker compose -f docker-compose.production.yml pull
```
* После успешной сборки на сервере выполните команды (только после первого деплоя):
    - Соберите статические файлы:
    ```
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    ```
    - Примените миграции:
    ```
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    ```
    - Создать суперпользователя Django:
    ```
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
    ```
