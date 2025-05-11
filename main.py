from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
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
PATH_TO_IMAGES = env.get('PATH_TO_IMAGES')

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
        
        unix_timestamp = int(time.time())
        img_path = f'{PATH_TO_IMAGES}{unix_timestamp}.jpeg'
        
        # Сохраняем изображение
        fig.write_image(img_path)
        logging.info(f"Изображение сохранено в {img_path}")
        
        # Открываем изображение
        with open(img_path, 'rb') as img_file:
            files = {'file': img_file}
            data = {'api_key': IMGHIPPO_API_KEY}
            
            # Добавляем заголовки, имитирующие браузер
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Добавляем небольшую задержку перед запросом
            time.sleep(1)
            
            logging.info("Отправка запроса на imghippo.com...")
            response = requests.post('https://api.imghippo.com/v1/upload', 
                                  data=data, 
                                  files=files, 
                                  headers=headers)
            
            logging.info(f"Ответ от imghippo.com: {response.status_code}")
            logging.info(f"Content-Type: {response.headers.get('Content-Type')}")
            logging.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    # Декодируем сжатый ответ
                    content = response.content
                    content_encoding = response.headers.get('Content-Encoding', '').lower()
                    logging.info(f"Content-Encoding: {content_encoding}")
                    
                    if content_encoding == 'br':
                        import brotli
                        try:
                            content = brotli.decompress(content)
                            logging.info("Успешно распаковано с помощью Brotli")
                        except Exception as e:
                            logging.error(f"Ошибка при распаковке Brotli: {str(e)}")
                            # Пробуем использовать raw content
                            content = response.content
                    elif content_encoding == 'gzip':
                        import gzip
                        try:
                            content = gzip.decompress(content)
                            logging.info("Успешно распаковано с помощью Gzip")
                        except Exception as e:
                            logging.error(f"Ошибка при распаковке Gzip: {str(e)}")
                            content = response.content
                    
                    # Пробуем декодировать как JSON
                    try:
                        response_data = json.loads(content)
                        logging.info(f"Успешно декодирован JSON: {response_data}")
                        if response_data.get('success'):
                            image_url = response_data['data']['url']
                            logging.info(f"Изображение успешно загружено: {image_url}")
                            return image_url
                        else:
                            error_msg = response_data.get('message', 'Неизвестная ошибка')
                            logging.error(f"Ошибка загрузки изображения: {error_msg}")
                            raise HTTPException(status_code=500, detail=f"Ошибка загрузки изображения: {error_msg}")
                    except json.JSONDecodeError as e:
                        logging.error(f"Ошибка декодирования JSON: {str(e)}")
                        logging.error(f"Содержимое ответа: {content[:500]}...")  # Логируем первые 500 символов
                        raise
                except Exception as e:
                    # Если ответ не JSON, пробуем получить URL из заголовков или тела ответа
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        # Если Content-Type указывает на JSON, но парсинг не удался
                        logging.error("Не удалось распарсить JSON ответ")
                        raise HTTPException(status_code=500, detail="Ошибка при обработке ответа от сервера")
                    else:
                        # Пробуем получить URL из заголовков или тела ответа
                        image_url = response.headers.get('Location') or content.decode('utf-8').strip()
                        if image_url:
                            # Проверяем, что URL валидный
                            if image_url.startswith(('http://', 'https://')):
                                logging.info(f"Изображение успешно загружено (не-JSON ответ): {image_url}")
                                return image_url
                            else:
                                # Если URL не начинается с http/https, пробуем декодировать как base64
                                try:
                                    import base64
                                    decoded_url = base64.b64decode(image_url).decode('utf-8')
                                    if decoded_url.startswith(('http://', 'https://')):
                                        logging.info(f"Изображение успешно загружено (base64 декодированный): {decoded_url}")
                                        return decoded_url
                                except:
                                    logging.error(f"Не удалось декодировать URL как base64: {image_url}")
                                    pass
                        raise HTTPException(status_code=500, detail="Не удалось получить валидный URL изображения из ответа")
            else:
                logging.error(f"Ошибка HTTP: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка загрузки изображения: {response.status_code}")
    except Exception as e:
        logging.error(f"Ошибка при работе с изображением: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при работе с изображением: {str(e)}")
    finally:
        # Удаляем временный файл
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                logging.info(f"Временный файл {img_path} удален")
        except Exception as e:
            logging.error(f"Ошибка при удалении временного файла: {str(e)}")


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
    try:
        data_dict = data.dict()
        
        # Получаем список значений из словаря
        data_lst = list(data_dict.values())

        # Теперь вы можете передать data_lst в функцию create_chart
        img_url = create_chart(data_lst)  # Сохраняем результат
        return {"imgUrl": img_url}  # Возвращаем URL изображения в виде словаря
    except Exception as e:
        log_error(e)  # Логируем ошибку
        raise HTTPException(status_code=500, detail="Ошибка при создании графика")
