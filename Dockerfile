# Используем официальный образ Python
FROM python:3.12 AS base

# Устанавливаем зависимости для Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false
# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями Poetry
COPY pyproject.toml poetry.lock /app/
# Устанавливаем зависимости с помощью Poetry
RUN poetry install --no-root

# Копируем весь код в контейнер
COPY . /app/

