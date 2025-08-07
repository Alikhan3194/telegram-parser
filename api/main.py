from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import telemetr
from api.logging_conf import setup_api_logging, LoggingMiddleware

# Настройка логирования
logger = setup_api_logging()

app = FastAPI(
    title="Telemetr Parser API",
    description="API для парсинга Telegram каналов с сайта telemetr.me",
    version="1.0.0"
)

# Добавляем middleware для логирования
app.add_middleware(LoggingMiddleware)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://6d3ff40450cc.ngrok-free.app",
    "hhttps://77575e4d233f.ngrok-free.app",
    ],
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Подключение роутеров
app.include_router(telemetr.router, prefix="/api")

@app.get("/")
def root():
    logger.info("Получен запрос к корневому эндпоинту")
    return {
        "message": "Telemetr Parser API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Telemetr Parser API запущен")
    logger.info("📊 Доступные эндпоинты:")
    logger.info("   PUT  /api/filters - обновление фильтров")
    logger.info("   POST /api/start - запуск парсера")
    logger.info("   GET  /api/status - статус парсера")
    logger.info("   GET  /api/download/{kind} - скачать результаты")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Telemetr Parser API остановлен")
