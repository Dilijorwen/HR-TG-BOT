FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1. ставим зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 2. копируем код бота
COPY bot/ ./bot
COPY bot/scripts/ ./scripts

# 3. команда запуска
CMD ["python", "-m", "uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]