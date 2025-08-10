import json
import pandas as pd
import logging
from pathlib import Path
import os
import importlib
import sys
from typing import Set

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
    from utils import build_listing_url, fetch_listing, extract_all_usernames, parse_channel_html, parse_channel_api, get_limits_from_html
except ImportError:
    from telemetr_parser.config import HEADERS, BASE_URL
    from telemetr_parser.utils import build_listing_url, fetch_listing, extract_all_usernames, parse_channel_html, parse_channel_api, get_limits_from_html

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


def _load_processed_usernames(file_path: Path) -> Set[str]:
    if file_path.exists():
        try:
            data = json.load(open(file_path, "r", encoding="utf-8"))
            if isinstance(data, list):
                return set(str(x) for x in data)
        except Exception:
            return set()
    return set()


def _save_processed_usernames(file_path: Path, usernames: Set[str]) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted(list(usernames)), f, ensure_ascii=False, indent=2)
    except Exception:
        pass


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
        start_page = FILTERS.get("start_page") or 1
        end_page = FILTERS.get("end_page")
        processed_file = data_dir / "processed_channels.json"
        processed_usernames: Set[str] = _load_processed_usernames(processed_file)
        channels_processed = 0
        total_found_on_pages = 0
        total_skipped_existing = 0
        
        logging.info(f"Начинаем парсинг с страницы {start_page}")
        logging.info(f"Файлы будут сохранены в: {data_dir.absolute()}")
        
        # Проверяем лимиты до старта - ТОЛЬКО gate лимиты могут остановить парсинг
        try:
            from telemetr_parser.utils import GATE_LIMIT_NAME
            limits = get_limits_from_html(HEADERS)
            for lim in limits:
                if lim.current <= 0:
                    if lim.severity == "gate" or lim.name == GATE_LIMIT_NAME:
                        raise Exception(f"Достигнут лимит: {lim.name} ({lim.description})")
                    else:
                        # Для нецелевых лимитов - только предупреждение
                        logging.warning(f"Достигнут нецелевой лимит: {lim.name} ({lim.description}) - продолжаем работу")
        except Exception as e:
            # Если это gate лимит - останавливаем
            if "Достигнут лимит:" in str(e):
                raise
            # Если не удалось получить лимиты, не блокируем запуск, но логируем
            logging.warning(f"Не удалось получить лимиты: {e}")

        # Готовим список допустимых параметров для build_listing_url (page пробрасывается отдельно)
        allowed_param_keys = {
            "categories","links","title","about","participants_from","participants_to",
            "views_post_from","views_post_to","er_from","er_to","mentions_week_from",
            "mentions_week_to","order_column","order_direction","channel_type",
            "moderate","verified","sex_m_from","sex_w_from","lang_code","lang_ru",
            "lang_uz","detailed_bot_added"
        }

        # Функция нормализации фильтров (убираем недопустимые ключи и внутренние служебные)
        def normalize_filters(src: dict) -> dict:
            return {k: v for k, v in src.items() if k in allowed_param_keys and v not in (None, "")}

        def process_single_page(page_number: int) -> bool:
            nonlocal channels_processed, total_found_on_pages, total_skipped_existing
            current_filters = normalize_filters(FILTERS)
            # page теперь идёт прямо в URL

            # Обновляем прогресс - текущая страница
            try:
                # Попытка импорта STATE - может не работать в зависимости от контекста
                import sys
                if 'api.routers.telemetr' in sys.modules:
                    from api.routers.telemetr import STATE
                    STATE["progress"]["current_page"] = page_number
                    STATE["progress"]["start_page"] = start_page
                    STATE["progress"]["end_page"] = end_page
            except Exception:
                pass  # Продолжаем работу даже если не удалось обновить прогресс

            try:
                url = build_listing_url(**current_filters, page=page_number)
                logging.info(f"Запрашиваем страницу {page_number}: {url}")

                soup = fetch_listing(url, HEADERS)
                usernames = extract_all_usernames(soup)

                if not usernames:
                    logging.info(f"На странице {page_number} не найдено каналов.")
                    return False

                logging.info(f"На странице {page_number} найдено {len(usernames)} каналов")
                total_found_on_pages += len(usernames)

                # Обновляем прогресс - количество каналов на странице
                try:
                    if 'api.routers.telemetr' in sys.modules:
                        from api.routers.telemetr import STATE
                        STATE["progress"]["channels_on_page"] = len(usernames)
                except Exception:
                    pass

                # фильтруем уже обработанные
                new_usernames = [u for u in usernames if u not in processed_usernames]
                skipped_existing = len(usernames) - len(new_usernames)
                total_skipped_existing += skipped_existing
                if skipped_existing:
                    logging.info(f"Пропущено уже обработанных каналов: {skipped_existing}")

                for i, uname in enumerate(new_usernames, 1):
                    # Проверка STOP_FLAG перед обработкой каждого канала
                    try:
                        if 'api.routers.telemetr' in sys.modules:
                            from api.routers.telemetr import STOP_FLAG
                            if STOP_FLAG.get("should_stop", False):
                                logging.info("Получен сигнал остановки пользователем")
                                return False
                    except Exception:
                        pass
                    
                    # Обновляем прогресс - текущий канал
                    try:
                        if 'api.routers.telemetr' in sys.modules:
                            from api.routers.telemetr import STATE
                            STATE["progress"]["channel_index"] = i
                    except Exception:
                        pass

                    try:
                        logging.info(f"Обрабатываем канал {i}/{len(new_usernames)} на странице {page_number}: {uname}")
                        try:
                            data = parse_channel_api(uname)
                        except Exception as e_api:
                            logging.warning(f"API не сработал для {uname}: {e_api}. Пытаемся HTML.")
                            data = parse_channel_html(uname, HEADERS)
                        results.append(data)
                        channels_processed += 1
                        processed_usernames.add(uname)

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
                    logging.info(f"Последняя страница {page_number} содержала {len(usernames)} каналов")
                    return False

                return True

            except Exception as e:
                error_msg = f"Ошибка при обработке страницы {page_number}: {e}"
                logging.error(error_msg)
                raise Exception(error_msg)

        # Переменная для отслеживания причины остановки
        stop_reason = None
        
        try:
            # Если указан end_page — ограниченный диапазон
            if end_page is not None:
                for p in range(start_page, end_page + 1):
                    # Проверка STOP_FLAG перед обработкой страницы
                    try:
                        if 'api.routers.telemetr' in sys.modules:
                            from api.routers.telemetr import STOP_FLAG
                            if STOP_FLAG.get("should_stop", False):
                                stop_reason = "Остановлено пользователем"
                                break
                    except Exception:
                        pass
                    
                    # Проверяем ТОЛЬКО gate лимиты перед обработкой страницы
                    try:
                        limits_before = get_limits_from_html(HEADERS)
                        for lim in limits_before:
                            if lim.current <= 0:
                                if lim.severity == "gate" or lim.name == GATE_LIMIT_NAME:
                                    stop_reason = f"⛔ Парсинг остановлен: достигнут лимит ({lim.name})"
                                    raise Exception(stop_reason)
                                else:
                                    # Для нецелевых лимитов - только предупреждение
                                    logging.warning(f"Достигнут нецелевой лимит: {lim.name} - продолжаем работу")
                    except Exception as e:
                        if "⛔" in str(e) or ("достигнут лимит" in str(e).lower() and lim.severity == "gate"):
                            stop_reason = str(e)
                            break
                        logging.warning(f"Не удалось проверить лимиты перед страницей {p}: {e}")
                    
                    should_continue = process_single_page(p)
                    if not should_continue:
                        break
            else:
                # Иначе — продолжаем до конца
                current_page = start_page
                while True:
                    # Проверка STOP_FLAG перед обработкой страницы
                    try:
                        if 'api.routers.telemetr' in sys.modules:
                            from api.routers.telemetr import STOP_FLAG
                            if STOP_FLAG.get("should_stop", False):
                                stop_reason = "Остановлено пользователем"
                                break
                    except Exception:
                        pass
                    
                    # Проверяем ТОЛЬКО gate лимиты перед обработкой страницы
                    try:
                        limits_before = get_limits_from_html(HEADERS)
                        for lim in limits_before:
                            if lim.current <= 0:
                                if lim.severity == "gate" or lim.name == GATE_LIMIT_NAME:
                                    stop_reason = f"⛔ Парсинг остановлен: достигнут лимит ({lim.name})"
                                    raise Exception(stop_reason)
                                else:
                                    # Для нецелевых лимитов - только предупреждение
                                    logging.warning(f"Достигнут нецелевой лимит: {lim.name} - продолжаем работу")
                    except Exception as e:
                        if "⛔" in str(e) or ("достигнут лимит" in str(e).lower() and lim.severity == "gate"):
                            stop_reason = str(e)
                            break
                        logging.warning(f"Не удалось проверить лимиты перед страницей {current_page}: {e}")
                    
                    should_continue = process_single_page(current_page)
                    if not should_continue:
                        break
                    current_page += 1
        except Exception as e:
            if "⛔" in str(e) or "Достигнут лимит" in str(e):
                stop_reason = str(e)
            else:
                raise

        # Выводим информацию о завершении
        if stop_reason:
            logging.warning(stop_reason)
            print(f"\n{stop_reason}")
        
        # Если есть результаты - сохраняем их
        if results:
            logging.info(f"Парсинг завершен. Обработано {channels_processed} каналов")
        elif not results and not stop_reason:
            if total_found_on_pages > 0 and total_skipped_existing >= total_found_on_pages:
                raise ValueError("Все найденные каналы на выбранных страницах уже были обработаны ранее")
            raise ValueError("Парсинг не вернул результатов. Возможно, фильтры слишком строгие или сайт недоступен.")
        
        # Сохранение файлов (даже если была остановка по лимитам)
        if results:
            json_path = data_dir / "telemetr_results.json"
            excel_path = data_dir / "telemetr_results.xlsx"
            _save_processed_usernames(processed_file, processed_usernames)
            
            # Сохраняем JSON
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                logging.info(f"JSON файл сохранен: {json_path}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении JSON файла: {e}")

            # Сохраняем Excel
            try:
                df = pd.DataFrame(results)
                df.to_excel(excel_path, index=False)
                logging.info(f"Excel файл сохранен: {excel_path}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении Excel файла: {e}")
            
            # Выводим информацию о сохраненных файлах
            if json_path.exists() and excel_path.exists():
                print(f"\n✅ Результаты сохранены:")
                print(f"- JSON: {json_path} ({json_path.stat().st_size} байт)")
                print(f"- Excel: {excel_path} ({excel_path.stat().st_size} байт)")
                print(f"- Всего каналов: {len(results)}")
            
        # Сбрасываем STOP_FLAG после завершения работы
        try:
            if 'api.routers.telemetr' in sys.modules:
                from api.routers.telemetr import STOP_FLAG
                STOP_FLAG["should_stop"] = False
        except Exception:
            pass
        
        # Если остановлены по лимитам или пользователем, но есть данные - не выбрасываем исключение
        if stop_reason and results:
            logging.info(f"Парсинг завершен с причиной: {stop_reason}. Данные сохранены.")
            return results
        
        return results
        
    except Exception as e:
        error_msg = f"Критическая ошибка парсинга: {e}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
        raise
    finally:
        try:
            # ensure progress saved even on errors
            pf = data_dir / "processed_channels.json"
            if 'processed_usernames' in locals() and processed_usernames:
                _save_processed_usernames(pf, processed_usernames)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        parse_all_channels()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit(1) 