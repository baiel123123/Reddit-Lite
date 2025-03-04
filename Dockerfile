# Используем официальный образ Python
FROM python:3.12

# Устанавливаем зависимости для Poetry
RUN pip install poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями Poetry
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости с помощью Poetry
RUN poetry install --no-interaction

# Копируем весь код в контейнер
COPY . /app/

# Запускаем FastAPI приложение через Uvicorn
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
