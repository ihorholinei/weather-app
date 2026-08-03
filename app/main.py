import os
import json
import httpx
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Weather API Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "weather_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Redis Connection
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                city VARCHAR(100),
                temperature FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

# Initialize Table on startup
init_db()

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
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis error: {e}")

    # 2. Якщо немає в кеші — запит до OpenWeather API
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API key is not configured")

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_key}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City not found")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")
        raw_data = response.json()

    # 3. Форматуємо відповідь чітко під JS-фронтенд
    formatted_data = {
        "city": raw_data.get("name", city.capitalize()),
        "temperature": raw_data["main"]["temp"],
        "feels_like": raw_data["main"]["feels_like"],
        "humidity": raw_data["main"]["humidity"],
        "wind_speed": raw_data["wind"]["speed"],
        "description": raw_data["weather"][0]["description"] if raw_data.get("weather") else ""
    }

    # 4. Зберігаємо в Redis (TTL = 600s)
    try:
        cache.setex(city_key, 600, json.dumps(formatted_data))
    except Exception as e:
        print(f"Redis save error: {e}")

    # 5. Логуємо запит + температуру в DB
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO search_history (city, temperature) VALUES (%s, %s);",
            (formatted_data["city"], formatted_data["temperature"])
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB log error: {e}")

    return formatted_data


@app.get("/history")
def get_history():
    """ Повертає останні 10 запитів для фронтенду """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT city, temperature, created_at AS requested_at 
            FROM search_history 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        history = cur.fetchall()
        cur.close()
        conn.close()
        return history
    except Exception as e:
        print(f"DB fetch history error: {e}")
        return []