from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from fastapi.responses import FileResponse
from typing import Literal
from pathlib import Path
import json
import logging

from api.schemas import FiltersSchema, LimitsResponse, LimitItem

router = APIRouter()
logger = logging.getLogger(__name__)

# Глобальное состояние парсера
STATE = {
    "running": False, 
    "error": None,
    "progress": {
        "current_page": None,
        "start_page": None,
        "end_page": None,
        "channel_index": None,
        "channels_on_page": None
    }
}
STOP_FLAG = {"should_stop": False}

@router.put("/filters", status_code=204)
def update_filters(body: FiltersSchema):
    """Write incoming JSON to telemetr_parser/filters_config.py"""
    try:
        logger.info(f"Получены фильтры для сохранения: {body.dict(exclude_none=True)}")
        
        # Конвертируем в словарь, исключая None значения
        incoming = body.dict(exclude_none=True)

        # Нормализуем ключи для build_listing_url
        filters_dict = {}
        mapping = {
            "channel_name": "title",
            "description": "about",
            "has_stats": "detailed_bot_added",
            "male_from": "sex_m_from",
            "female_from": "sex_w_from",
        }
        for k, v in incoming.items():
            if k == "page":
                # удаляем page — задается программно
                continue
            if k in ("start_page", "end_page"):
                # сохраняем как есть — используются в парсере, но не передаются в URL
                filters_dict[k] = v
                continue
            key = mapping.get(k, k)
            filters_dict[key] = v
        
        # Путь к файлу конфигурации
        config_path = Path("telemetr_parser/filters_config.py")
        
        # Создаем содержимое файла
        filters_content = json.dumps(filters_dict, ensure_ascii=False, indent=2)
        content = f"""# filters_config.py

# Настройки фильтрации — автоматически обновлены из веб-формы
FILTERS = {filters_content}
"""
        
        # Записываем в файл
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Фильтры успешно сохранены в {config_path}")
        return Response(status_code=204)
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении фильтров: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения фильтров: {str(e)}")

@router.post("/start", status_code=202)
def start_parse(bg: BackgroundTasks):
    """Запуск парсера в фоновом режиме"""
    if STATE["running"]:
        raise HTTPException(status_code=409, detail="Parser already running")
    
    logger.info("Запуск парсера")
    STATE.update({
        "running": True, 
        "error": None,
        "progress": {
            "current_page": None,
            "start_page": None,
            "end_page": None,
            "channel_index": None,
            "channels_on_page": None
        }
    })
    STOP_FLAG["should_stop"] = False
    bg.add_task(_run)
    
    return {"msg": "started"}

@router.post("/stop", status_code=202)
def stop_parse():
    """Остановка парсера"""
    if not STATE["running"]:
        raise HTTPException(status_code=409, detail="Parser not running")
    
    logger.info("Запрос на остановку парсера")
    STOP_FLAG["should_stop"] = True
    
    return {"msg": "stop requested"}

def _run():
    """Фоновая функция для запуска парсера"""
    try:
        logger.info("Начинаем выполнение парсинга")
        
        # Принудительно перезагружаем модуль с фильтрами
        import importlib
        import sys
        if 'telemetr_parser.filters_config' in sys.modules:
            importlib.reload(sys.modules['telemetr_parser.filters_config'])
            logger.info("Модуль filters_config перезагружен")
        
        # Импортируем функцию парсинга
        from telemetr_parser.main import parse_all_channels
        
        # Запускаем парсинг
        result = parse_all_channels()
        
        logger.info(f"Парсинг завершен успешно. Обработано {len(result) if result else 0} каналов")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при выполнении парсинга: {error_msg}")
        STATE["error"] = error_msg
    finally:
        STATE["running"] = False
        logger.info("Парсер остановлен")

@router.get("/status")
def status():
    """Получение текущего статуса парсера"""
    # Дополнительно можно вернуть свежие лимиты
    return STATE


@router.get("/limits", response_model=LimitsResponse)
def get_limits():
    """Возвращает текущие лимиты пользователя, спарсенные из HTML профиля."""
    try:
        # Импортируем парсер лимитов
        from telemetr_parser.config import HEADERS
        from telemetr_parser.utils import get_limits_from_html

        limits = get_limits_from_html(HEADERS)
        items = [LimitItem(
            name=l.name, 
            description=l.description, 
            current=l.current, 
            maximum=l.maximum,
            severity=l.severity
        ) for l in limits]
        return LimitsResponse(items=items)
    except Exception as e:
        logger.error(f"Ошибка при получении лимитов: {e}")
        raise HTTPException(status_code=500, detail=f"Не удалось получить лимиты: {str(e)}")

@router.get("/files-info")
def files_info():
    """Информация о доступных файлах"""
    excel_path = Path("data/telemetr_results.xlsx")
    json_path = Path("data/telemetr_results.json")
    
    return {
        "excel": {
            "exists": excel_path.exists(),
            "size": excel_path.stat().st_size if excel_path.exists() else 0
        },
        "json": {
            "exists": json_path.exists(),
            "size": json_path.stat().st_size if json_path.exists() else 0
        }
    }

@router.get("/download/{kind}", response_class=FileResponse)
@router.head("/download/{kind}")
def download_file(kind: Literal["excel", "json"]):
    """Скачивание файлов результатов"""
    try:
        # Определяем имя файла
        if kind == "excel":
            filename = "data/telemetr_results.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:  # json
            filename = "data/telemetr_results.json"
            media_type = "application/json"
        
        file_path = Path(filename)
        
        # Проверяем существование файла
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Файл {filename} не найден")
        
        # Проверяем размер файла
        if file_path.stat().st_size == 0:
            raise HTTPException(status_code=404, detail=f"Файл {filename} пустой")
        
        logger.info(f"Отправка файла: {filename} (размер: {file_path.stat().st_size} байт)")
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=media_type,
            headers={
                "Cache-Control": "no-store",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла {kind}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания: {str(e)}")
