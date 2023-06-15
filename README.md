![example workflow](https://github.com/SidVi990/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
# Foodgram

## Описание:

Foodgram - продуктовый помощник с с помощью которого можно делиться рецептами с другими пользователями или открывать для себя что-то новое. Здесь можно сохранять избранное, подписываться на понравившихся авторов а также формировать список продуктов для приготовления понравившихся рецептов.

В документации описаны возможные запросы к API и структура ожидаемых ответов. Для каждого запроса указаны уровни прав доступа.

## Стек технологий:
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)

![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

## Как запустить проект:

- Склонируйте репозитрий на свой компьютер или удаленный сервер.

 - Установите docker на сервер:

```
sudo apt install docker.io
```

- Установите docker-compose на сервер:

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
- Локально отредактируйте файл infra/nginx.conf и в строке server_name впишите свой IP

- Создайте .env файл в директории infra/, в котором должны содержаться следующие переменные:

> DB_ENGINE=django.db.backends.postgresql

> DB_NAME= # название БД\ 

> POSTGRES_USER= # имя пользователя

> POSTGRES_PASSWORD= # пароль для доступа к БД

> DB_HOST=db

> DB_PORT=5432

- Из папки `infra/` соберите образ при помощи docker compose `$ docker compose up -d`

- Создайте и примените миграции `$ docker compose exec backend python manage.py makemigrations`, а затем `$ docker compose exec backend python manage.py migrate`

- Соберите статику `$ docker compose exec backend python manage.py collectstatic --no-input`

- Для доступа к админке не забудьте создать суперюзера `$ docker compose exec backend python manage.py createsuperuser`

- Развернутый проект будет доступен по IP вашего сервера.

## Автор backend'а:

[Евгений Малый](https://github.com/SidVi990)
