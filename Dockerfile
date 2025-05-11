# Используем официальный образ Python
FROM python:3.11

# Устанавливаем рабочую директорию
WORKDIR /app


# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы
COPY . .

# Открываем порт, который слушает Uvicorn (Render использует 0.0.0.0:10000+)
EXPOSE 8080

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--por]()
