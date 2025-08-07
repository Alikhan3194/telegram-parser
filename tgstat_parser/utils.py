import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode


def build_listing_url(
    *,
    categories: list[str]   = None,  # адаптировать под tgstat категории
    keywords:   str         = None,  # поиск по ключевым словам
    subscribers_from: int   = None,
    subscribers_to:   int   = None,
    posts_per_day_from: int = None,
    posts_per_day_to:   int = None,
    order:              str = None,  # "subscribers", "posts_per_day", "er", etc.
    page:               int = None,
    lang:               str = None,  # "ru", "en", "all"
) -> str:
    """
    Строит URL для поиска каналов на tgstat.ru
    Нужно адаптировать под реальную структуру tgstat API
    """
    base = "https://tgstat.ru/channels"
    
    params = {
        "category":          ",".join(categories) if categories else None,
        "keywords":          keywords,
        "subscribers_from":  subscribers_from,
        "subscribers_to":    subscribers_to,
        "posts_per_day_from": posts_per_day_from,
        "posts_per_day_to":   posts_per_day_to,
        "order":             order,
        "page":              page,
        "lang":              lang,
    }
    
    clean = {k: v for k, v in params.items() if v not in (None, "")}
    return base + ("?" + urlencode(clean, doseq=True) if clean else "")


def fetch_listing(url, headers):
    """
    Получает HTML страницы со списком каналов tgstat
    """
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_first_n_usernames(soup, n=5):
    """
    Извлекает первые N юзернеймов каналов из HTML tgstat
    Нужно адаптировать селекторы под реальную разметку tgstat
    """
    # TODO: Адаптировать селекторы под tgstat.ru
    # Примерные селекторы (нужно проверить реальную разметку)
    rows = soup.select(".channel-item") or soup.select("tr") or soup.select(".channel")
    usernames = []
    
    for item in rows:
        if len(usernames) >= n:
            break
        
        # TODO: Найти правильный селектор для ссылки на канал
        link = item.select_one("a[href*='@']") or item.select_one("a[href*='t.me']")
        if link:
            href = link.get("href", "")
            # Извлекаем username из ссылки
            if "@" in href:
                username = href.split("@")[-1].split("/")[0]
                if username:
                    usernames.append(username)
    
    return usernames


def parse_channel(username, headers):
    """
    Парсит детальную страницу канала на tgstat
    Нужно адаптировать под структуру tgstat
    """
    url = f"https://tgstat.ru/channel/@{username}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # TODO: Адаптировать селекторы под tgstat.ru
    # Примерная структура (нужно проверить реальную разметку)
    
    # Название канала
    title_elem = soup.select_one("h1") or soup.select_one(".channel-title")
    title = title_elem.get_text(strip=True) if title_elem else "N/A"
    
    # Ссылка на Telegram
    tg_link = f"https://t.me/{username}"
    tg_username = f"@{username}"
    
    # Количество подписчиков
    sub_elem = soup.select_one(".subscribers") or soup.select_one("[data-subscribers]")
    subscribers = sub_elem.get_text(strip=True) if sub_elem else "N/A"
    
    # Описание канала
    desc_elem = soup.select_one(".description") or soup.select_one(".channel-description")
    description = []
    if desc_elem:
        desc_text = desc_elem.get_text(strip=True)
        if desc_text:
            description.append((desc_text, None))
    
    # Админы (если есть информация)
    admins = None
    admin_elems = soup.select(".admin") or soup.select("[data-admin]")
    if admin_elems:
        admins = []
        for admin in admin_elems:
            admin_text = admin.get_text(strip=True)
            admin_link = admin.get("href")
            if admin_text:
                admins.append((admin_text, admin_link))
    
    return {
        "title":       title,
        "tg_link":     tg_link,
        "tg_username": tg_username,
        "subscribers": subscribers,
        "description": description,
        "admins":      admins
    } 