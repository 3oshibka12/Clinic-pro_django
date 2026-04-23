FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для работы с PDF (шрифты и т.д.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для временных PDF (как просил коллега)
RUN mkdir -p /tmp/pdf_cache

# Просто запускаем скрипт
CMD ["python", "main.py"]