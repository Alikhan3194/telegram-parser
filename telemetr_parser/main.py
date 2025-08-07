import json
import pandas as pd
import logging
from pathlib import Path
import os
import importlib
import sys

def get_current_filters():
    """Динамически загружает текущие фильтры"""
    try:
        if 'telemetr_parser.filters_config' in sys.modules:
            importlib.reload(sys.modules['telemetr_parser.filters_config'])
        elif 'filters_config' in sys.modules:
            importlib.reload(sys.modules['filters_config'])
        
        try:
            from filters_config import FILTERS
            return FILTERS
        except ImportError:
            from telemetr_parser.filters_config import FILTERS
            return FILTERS
    except Exception as e:
        logging.error(f"Ошибка загрузки фильтров: {e}")
        return {}

try:
    from config import HEADERS, BASE_URL
    from utils import build_listing_url, fetch_listing, extract_all_usernames, parse_channel
except ImportError:
    from telemetr_parser.config import HEADERS, BASE_URL
    from telemetr_parser.utils import build_listing_url, fetch_listing, extract_all_usernames, parse_channel

logs_dir = Path("../logs")
logs_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=logs_dir / "telemetr_missing.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
if os.path.basename(os.getcwd()) == "telemetr_parser":
    data_dir = Path("../data")
else:
    data_dir = Path("data")

data_dir.mkdir(exist_ok=True)


def parse_all_channels():
    """
    Основная функция парсинга всех каналов с использованием настроек из filters_config.py
    
    Returns:
        list: Список данных о каналах
        
    Raises:
        Exception: При любых ошибках в процессе парсинга
    """
    logging.info("Начинается парсинг каналов...")
    
    try:
        FILTERS = get_current_filters()
        if not FILTERS:
            raise ValueError("Фильтры не настроены в filters_config.py")
        
        logging.info(f"Используемые фильтры: {FILTERS}")
        
        results = []
        page = FILTERS.get("page", 1)
        channels_processed = 0
        
        logging.info(f"Начинаем парсинг с страницы {page}")
        logging.info(f"Файлы будут сохранены в: {data_dir.absolute()}")
        
        while True:
            current_filters = FILTERS.copy()
            current_filters["page"] = page
            
            try:
                url = build_listing_url(**current_filters)
                logging.info(f"Запрашиваем страницу {page}: {url}")
                
                soup = fetch_listing(url, HEADERS)
                usernames = extract_all_usernames(soup)  
                
                if not usernames:
                    logging.info(f"На странице {page} не найдено каналов. Завершаем парсинг.")
                    break

                logging.info(f"На странице {page} найдено {len(usernames)} каналов")

                for i, uname in enumerate(usernames, 1):
                    try:
                        logging.info(f"Обрабатываем канал {i}/{len(usernames)} на странице {page}: {uname}")
                        data = parse_channel(uname, HEADERS)
                        results.append(data)
                        channels_processed += 1
                        
                        print("-"*40)
                        print(f"[{channels_processed}] Название: ", data["title"])
                        print("TG ссылка:  ", data["tg_link"])
                        print("Юзернейм:   ", data["tg_username"])
                        print("Подписчики: ", data["subscribers"])
                        print("Описание:")
                        for text, link in data["description"]:
                            print("  •", text, end="")
                            if link:
                                print(f" ({link})")
                            else:
                                print()
                        print("Админы:     ", data["admins"])
                        print()
                        
                    except Exception as e:
                        error_msg = f"Ошибка при обработке канала {uname}: {e}"
                        logging.error(error_msg)
                        print(f"⚠️ Пропускаем канал {uname}: {e}")
                        # Продолжаем обработку других каналов

                # если на странице было меньше 30 каналов — дальше нечего парсить
                if len(usernames) < 30:
                    logging.info(f"Последняя страница {page} содержала {len(usernames)} каналов")
                    break
                    
                page += 1
                
            except Exception as e:
                error_msg = f"Ошибка при обработке страницы {page}: {e}"
                logging.error(error_msg)
                raise Exception(error_msg)

        # Проверяем, что получены результаты
        if not results:
            raise ValueError("Парсинг не вернул результатов. Возможно, фильтры слишком строгие или сайт недоступен.")
        
        logging.info(f"Парсинг завершен. Обработано {channels_processed} каналов из {page-1} страниц")
        
        # Сохранение файлов
        json_path = data_dir / "telemetr_results.json"
        excel_path = data_dir / "telemetr_results.xlsx"
        
        # Сохраняем JSON
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logging.info(f"JSON файл сохранен: {json_path}")
        except Exception as e:
            raise Exception(f"Ошибка при сохранении JSON файла: {e}")

        # Сохраняем Excel
        try:
            df = pd.DataFrame(results)
            df.to_excel(excel_path, index=False)
            logging.info(f"Excel файл сохранен: {excel_path}")
        except Exception as e:
            raise Exception(f"Ошибка при сохранении Excel файла: {e}")
        
        # Проверяем, что файлы действительно созданы и не пустые
        if not json_path.exists() or json_path.stat().st_size == 0:
            raise Exception("JSON файл не создан или пустой")
            
        if not excel_path.exists() or excel_path.stat().st_size == 0:
            raise Exception("Excel файл не создан или пустой")
        
        print(f"\n✅ Результаты сохранены:")
        print(f"- JSON: {json_path} ({json_path.stat().st_size} байт)")
        print(f"- Excel: {excel_path} ({excel_path.stat().st_size} байт)")
        print(f"- Всего каналов: {len(results)}")
        
        return results
        
    except Exception as e:
        error_msg = f"Критическая ошибка парсинга: {e}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
        raise


if __name__ == "__main__":
    try:
        parse_all_channels()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit(1) 