# 🔍 Telemetr Парсер - Парсер Telegram каналов

Удобная система для парсинга Telegram-каналов с сайта telemetr.me с веб-интерфейсом.

## 🏗️ Архитектура проекта

```
📁 Проект/
├── 🐍 telemetr_parser/          # Основной парсер
│   ├── config.py                # Конфигурация (headers, URL)
│   ├── filters_config.py        # ✨ ФИЛЬТРЫ - редактируете здесь!
│   ├── main.py                  # Основной скрипт парсера
│   ├── utils.py                 # Вспомогательные функции
│   └── __init__.py              # Пакет Python
├── 🚀 api/                      # Backend API
│   ├── main.py                  # FastAPI приложение
│   ├── parser_logic.py          # Логика запуска парсера
│   └── routers/
│       └── telemetr.py          # API роуты
├── 🎨 telemetr-ui/              # Frontend интерфейс
│   ├── src/
│   │   └── App.jsx              # Главный компонент
│   └── package.json
└── 📊 data/                     # Результаты парсинга
    ├── telemetr_results.xlsx
    └── telemetr_results.json
```

## ✨ Основные возможности

✅ **Простая настройка фильтров** - редактируйте `filters_config.py`  
✅ **Веб-интерфейс** - удобное управление через браузер  
✅ **Фоновый парсинг** - парсинг идет в фоне, не блокирует интерфейс  
✅ **Два формата результатов** - Excel и JSON  
✅ **Автоматическая пагинация** - парсит все страницы результатов  

## 🚀 Быстрый старт

### 1️⃣ Настройка фильтров

Откройте файл `telemetr_parser/filters_config.py` и настройте нужные фильтры:

```python
FILTERS = {
    "categories": ["Прогнозы и ставки"],     # Категории каналов
    "participants_from": 5000,               # Мин. количество подписчиков
    "participants_to": 100000,               # Макс. количество подписчиков
    "er_from": 10,                          # Мин. уровень вовлеченности
    "mentions_week_from": 5,                # Мин. упоминаний в неделю
    "page": 1                               # Стартовая страница
}
```

**Доступные параметры фильтрации:**
- `categories` - категории каналов
- `links` - список каналов для поиска
- `title` - фильтр по названию канала
- `about` - фильтр по описанию канала
- `participants_from/to` - диапазон подписчиков
- `views_post_from/to` - диапазон просмотров постов
- `er_from/to` - диапазон уровня вовлеченности
- `mentions_week_from/to` - диапазон упоминаний в неделю
- `order_column` - сортировка ("participants_count", etc.)
- `order_direction` - направление ("ASC" или "DESC")
- `channel_type` - тип канала ("opened", "closed", "all")
- `moderate` - модерация ("yes", "no", "all")
- `verified` - верификация ("yes", "no", "all")
- И многие другие...

### 2️⃣ Запуск Backend

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ Запуск Frontend

```bash
cd telemetr-ui
npm install
npm run dev
```

### 4️⃣ Использование

1. 🌐 Откройте http://localhost:5173 в браузере
2. 🚀 Нажмите "Запустить парсер"
3. ⏳ Дождитесь завершения парсинга
4. 📥 Скачайте результаты в нужном формате

## 🛠️ Ручной запуск парсера

Можно запустить парсер напрямую без веб-интерфейса:

```bash
cd telemetr_parser
python main.py
```

## 📊 Результаты парсинга

Результаты сохраняются в папке `data/`:

- **Excel файл** (`telemetr_results.xlsx`) - для анализа и отчетов
- **JSON файл** (`telemetr_results.json`) - для программной обработки

### Структура данных:

```json
{
  "title": "Название канала",
  "tg_link": "https://t.me/channel",
  "tg_username": "@channel",
  "subscribers": "50,000",
  "description": [["Описание канала", "https://link.com"]],
  "admins": [["Админ канала", "@admin"]]
}
```

## 🔧 API Endpoints

- `POST /api/start` - Запуск парсера
- `GET /api/status` - Проверка статуса парсера
- `GET /api/download/excel` - Скачать Excel файл
- `GET /api/download/json` - Скачать JSON файл

## 🎯 Примеры использования

### Поиск каналов по спорту с высокой активностью:
```python
FILTERS = {
    "categories": ["Спорт"],
    "participants_from": 10000,
    "er_from": 15,
    "mentions_week_from": 10
}
```

### Поиск крупных IT каналов:
```python
FILTERS = {
    "categories": ["IT"],
    "participants_from": 50000,
    "participants_to": 500000,
    "order_column": "participants_count",
    "order_direction": "DESC"
}
```

### Поиск конкретных каналов:
```python
FILTERS = {
    "links": ["@durov", "@telegram"],
    "participants_from": 1000
}
```

## 📝 Логирование

Логи парсера сохраняются в `logs/telemetr_missing.log`

## 🚨 Важные примечания

- ⚠️ Соблюдайте правила сайта telemetr.me при парсинге
- 🕐 Парсинг может занять время в зависимости от количества каналов
- 🔄 Фильтры применяются сразу после изменения `filters_config.py`
- 🛡️ Убедитесь, что API запущен перед использованием веб-интерфейса

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте, что все зависимости установлены
2. Убедитесь, что Backend и Frontend запущены
3. Проверьте логи в папке `logs/`
4. Убедитесь в корректности настроек в `filters_config.py`

---

**Удачного парсинга! 🎉**
