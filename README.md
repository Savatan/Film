# Film

Веб-приложение для работы с каталогом фильмов и сбора данных из внешних источников.

## Технологии

![Python](https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-4169e1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-d71f00)
![Docker](https://img.shields.io/badge/Docker-containers-2496ed?logo=docker&logoColor=white)

## О проекте

Проект объединяет веб-приложение, работу с данными о фильмах и инструменты сбора информации из внешних источников.

## Основные компоненты

- `app/` — основное приложение и веб-интерфейс.
- `backend/` — backend-компоненты и зависимости.
- `database/` — материалы, связанные с базой данных.
- `Dockerfile` — сборка контейнера.
- `.env.example` — шаблон переменных окружения.

## Используемые инструменты

- **FastAPI** и **SQLAlchemy** — серверная часть и работа с данными.
- **PostgreSQL** — база данных.
- **RapidFuzz** — нечёткое сравнение строк.
- **Requests** и **BeautifulSoup** — HTTP-запросы и разбор HTML.
- **Jinja2** — шаблоны веб-интерфейса.
- **Docker** — контейнеризация.

## Запуск

В репозитории есть скрипт `START.sh` и Dockerfile. Перед запуском настройте переменные окружения на основе `.env.example`, включая подключение к PostgreSQL, затем проверьте актуальные команды в скрипте запуска.

> Не добавляйте реальные ключи API и пароли в репозиторий.
