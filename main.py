from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.responses import JSONResponse
from os import environ as env
from pydantic import BaseModel
import io
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import sys
import time
import os
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.staticfiles import StaticFiles

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменяем уровень на DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Добавляем тестовое сообщение при запуске
logging.info("="*50)
logging.info("Сервер запущен")
logging.info(f"Текущая директория: {os.getcwd()}")
logging.info(f"Права на app.log: {oct(os.stat('app.log').st_mode)[-3:]}")
logging.info("="*50)

app = FastAPI()

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    logging.info("="*50)
    logging.info(f"Входящий запрос: {request.method} {request.url}")
    logging.info(f"Заголовки: {dict(request.headers)}")
    
    # Получаем тело запроса
    try:
        body = await request.body()
        body_str = body.decode() if body else "Пустое тело"
        logging.info(f"Тело запроса: {body_str}")
        
        # Пробуем распарсить как JSON
        try:
            body_json = json.loads(body_str)
            logging.info(f"Тело запроса (JSON): {json.dumps(body_json, ensure_ascii=False)}")
        except:
            logging.info("Тело запроса не является валидным JSON")
    except Exception as e:
        logging.error(f"Ошибка при чтении тела запроса: {str(e)}")
    
    response = await call_next(request)
    
    # Логируем время выполнения
    process_time = time.time() - start_time
    logging.info(f"Время выполнения: {process_time:.2f} секунд")
    logging.info("="*50)
    
    return response

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

IMGHIPPO_API_KEY = env.get('IMGHIPPO_API_KEY')

class ChartData(BaseModel):
    team_solving_x2: int
    stakeholders_solving_x2: int
    approach_solving_x2: int
    planning_solving_x2: int
    measurement_solving_x2: int
    risks_solving_x2: int
    team_tools: int
    stakeholders_tools: int
    approach_tools: int
    planning_tools: int
    measurement_tools: int
    risks_tools: int


def create_chart(result_lst):
    try:
        # Создаем два отдельных DataFrame и объединяем их
        df1 = pd.DataFrame({
            'category': ['Команда', 'Заинт. стороны', 'Подход и поставка', 'Планирование', 
                         'Работа и измерение', 'Риски'],
            'Аспект': ['проблемы'] * 6,
            'score': result_lst[:6]
        })
        
        df2 = pd.DataFrame({
            'category': ['Команда', 'Заинт. стороны', 'Подход и поставка', 'Планирование', 
                         'Работа и измерение', 'Риски'],
            'Аспект': ['компетенции'] * 6,
            'score': result_lst[6:]
        })
        
        df = pd.concat([df1, df2], ignore_index=True)

        # Устанавливаем совместимые типы для категорий
        conditions = [
            (df['score'] == 0),
            (df['score'] >= 1) & (df['score'] <= 6),
            (df['score'] >= 7) & (df['score'] <= 12),
            (df['score'] >= 13) & (df['score'] <= 20)
        ]

        tiers = ['Новичок', 'Падаван', 'Рыцарь-Джедай', 'Мастер-Джедай']
        
        # Обеспечиваем, что все категории - строки
        df['mark'] = np.select(conditions, tiers, default='Неизвестный уровень')

        # Приведение к категориальному типу
        df['mark'] = df['mark'].astype(str)

        score = sum(result_lst)
        level = ''

        if 0 <= score <= 41:
            level = 'Новичок'
        elif 42 <= score <= 50:
            level = 'Падаван'
        elif 51 <= score <= 70:
            level = "Двигаетесь от Падавана к Рыцарю-Джедаю"
        elif 71 <= score <= 100:
            level = 'Рыцарь-Джедай'
        else:
            level = 'Мастер-Джедай'

        fig = px.line_polar(df, r="score", theta="category", color="Аспект", line_close=True,
                             color_discrete_sequence=['#3b5998', '#52a9f9'],
                             title=f"Всего очков: {score}, {level}")

        fig.update_traces(fill='toself')
        fig.update_layout(polar={"radialaxis": {"tickmode": "array", "tickvals": [0, 7, 12, 20],
                                                  "ticktext": ['Новичок', 'Падаван', 'Рыцарь-Джедай', 'Мастер-Джедай'],
                                                  "range": [0, 20]}})
        
        # Создаем временный файл в /tmp
        unix_timestamp = int(time.time())
        img_path = f'/tmp/{unix_timestamp}.jpeg'
        
        # Сохраняем изображение
        fig.write_image(img_path)
        logging.info(f"Изображение сохранено во временный файл: {img_path}")
        
        return img_path  # Возвращаем путь к файлу вместо URL
        
    except Exception as e:
        logging.error(f"Ошибка при работе с изображением: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при работе с изображением: {str(e)}")


@app.get("/")
async def get_root():
    page = """
    <!DOCTYPE html>
    <html>
        <head>
            <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
            <title>Tripwire Plotter API</title>
        </head>
        <body>
            <h1>Привет, это API tripwire-бота: @infostart_mt_course_bot</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=page)

@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("static/favicon.ico")


@app.post("/chart/")
async def build_chart(data: ChartData):
    img_path = None
    try:
        data_dict = data.dict()
        data_lst = list(data_dict.values())
        
        # Получаем путь к файлу
        img_path = create_chart(data_lst)
        
        # Проверяем существование файла перед отправкой
        if not os.path.exists(img_path):
            raise HTTPException(status_code=500, detail="Файл изображения не был создан")
            
        # Читаем содержимое файла
        with open(img_path, 'rb') as f:
            image_data = f.read()
            
        # Удаляем файл после чтения
        os.remove(img_path)
        logging.info(f"Временный файл {img_path} удален")
        
        # Возвращаем содержимое файла напрямую
        return Response(
            content=image_data,
            media_type='image/jpeg',
            headers={
                'Content-Disposition': 'attachment; filename="chart.jpeg"'
            }
        )
        
    except Exception as e:
        logging.error(f"Ошибка при создании графика: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при создании графика")
    finally:
        # Удаляем файл, если он все еще существует
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
                logging.info(f"Временный файл {img_path} удален в блоке finally")
            except Exception as e:
                logging.error(f"Ошибка при удалении временного файла: {str(e)}")
