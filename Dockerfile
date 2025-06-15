FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY db ./db

ENV PYTHONPATH=/app
CMD ["python", "-m", "bot.main"]