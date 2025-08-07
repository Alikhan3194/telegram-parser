import logging
import time
from pathlib import Path
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Создаем папку для логов
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Настройка логгера для API
def setup_api_logging():
    """Настройка логирования для API"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Создаем файловый хендлер
    file_handler = logging.FileHandler(
        logs_dir / "api.log", 
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Создаем консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех HTTP запросов и ответов"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api.requests")
    
    async def dispatch(self, request: Request, call_next):
        # Логируем входящий запрос
        start_time = time.time()
        
        # Получаем информацию о запросе
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        self.logger.info(f"🔵 {method} {url} - Client: {client_ip}")
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            
            # Вычисляем время выполнения
            process_time = time.time() - start_time
            
            # Логируем ответ
            status_code = response.status_code
            
            # Определяем уровень логирования на основе статуса
            if status_code >= 500:
                log_level = "ERROR"
                emoji = "🔴"
            elif status_code >= 400:
                log_level = "WARNING"
                emoji = "🟡"
            else:
                log_level = "INFO"
                emoji = "🟢"
            
            self.logger.log(
                getattr(logging, log_level),
                f"{emoji} {method} {url} - {status_code} - {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Логируем исключения
            process_time = time.time() - start_time
            self.logger.error(
                f"🔴 {method} {url} - EXCEPTION: {str(e)} - {process_time:.3f}s"
            )
            raise 