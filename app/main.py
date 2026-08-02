import os
import json
import httpx
import redis
import psycopg2
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Weather API Service")

# Конфігурація з зміних оточення (Environment Variables)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "weather_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Підключення до Redis
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Weather API"}

@app.get("/weather")
async def get_weather(city: str):
    if not city:
        raise HTTPException(status_code=400, detail="City name is required")
    
    city_key = city.lower().strip()

    # 1. Перевірка кешу в Redis
    try:
        cached_data = cache.get(city_key)
        if cached_data:
            return {"source": "cache", "data": json.loads(cached_data)}
    except Exception as e:
        print(f"Redis error: {e}")

    # 2. Якщо в кеші немає — ідемо в OpenWeather API
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API key is not configured")

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_key}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")
        weather_data = response.json()

    # 3. Зберігаємо результат у Redis (TTL = 600 сек)
    try:
        cache.setex(city_key, 600, json.dumps(weather_data))
    except Exception as e:
        print(f"Redis save error: {e}")

    # 4. Логуємо запит у PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS search_history (id SERIAL PRIMARY KEY, city VARCHAR(100), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
        )
        cur.execute("INSERT INTO search_history (city) VALUES (%s);", (city_key,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB log error: {e}")

    return {"source": "api", "data": weather_data}