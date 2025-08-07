import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode

try:
    # Попытка относительного импорта (когда запускаем из telemetr_parser/)
    from config import BASE_URL
except ImportError:
    # Абсолютный импорт (когда запускаем из корня проекта)
    from telemetr_parser.config import BASE_URL


def build_listing_url(
    *,
    categories: list[str]   = None,  # ["GIF и video","IT","SMM","Авто и мото"]
    links:      list[str]   = None,  # ["@fintopiochannel","@hamster_kombat"]
    title:      str         = None,  # фильтр по названию канала
    about:      str         = None,  # фильтр по описанию канала
    participants_from: int  = None,
    participants_to:   int  = None,
    views_post_from:   int  = None,
    views_post_to:     int  = None,
    er_from:           int  = None,
    er_to:             int  = None,
    mentions_week_from:int  = None,
    mentions_week_to:  int  = None,
    order_column:      str  = None,  # e.g. "participants_count"
    order_direction:   str  = None,  # "ASC" или "DESC"
    page:              int  = None,
    channel_type:      str  = None,  # "opened"/"closed"/"all"
    moderate:          str  = None,  # "yes"/"no"/"all"
    verified:          str  = None,  # "yes"/"no"/"all"
    sex_m_from:        int  = None,
    sex_w_from:        int  = None,
    lang_code:         str  = None,  # "any","ru","ua"...
    lang_ru:           int  = None,  # 1/0
    lang_uz:           int  = None,  # 1/0
    detailed_bot_added:str  = None,  # "yes"/"no"/"all"
) -> str:
    # если есть категории — /channels/cat/.../, иначе — просто /channels/
    if categories:
        cats = quote(",".join(categories), safe=",")
        base = f"https://telemetr.me/channels/cat/{cats}/"
    else:
        base = "https://telemetr.me/channels/"

    params = {
        "links":              "\r\n".join(links) if links else None,
        "title":              title,
        "about":              about,                  #
        "participants_from":  participants_from,
        "participants_to":    participants_to,
        "views_post_from":    views_post_from,
        "views_post_to":      views_post_to,
        "er_from":            er_from,
        "er_to":              er_to,
        "mentions_week_from": mentions_week_from,
        "mentions_week_to":   mentions_week_to,
        "order_column":       order_column,
        "order_direction":    order_direction,
        "page":               page,
        "channel_type":       channel_type,
        "moderate":           moderate,
        "verified":           verified,
        "sex_m_from":         sex_m_from,
        "sex_w_from":         sex_w_from,
        "lang_code":          lang_code,
        "lang_ru":            lang_ru,
        "lang_uz":            lang_uz,
        "detailed_bot_added": detailed_bot_added,
    }

    clean = {k: v for k, v in params.items() if v not in (None, "")}
    return base + ("?" + urlencode(clean, doseq=True) if clean else "")


def fetch_listing(url, headers):
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_all_usernames(soup):
    """Вернуть все пути (/ @… или /joinchat/…) со страницы каталога."""
    rows = soup.select("#channels_table tbody tr")
    result = []
    for tr in rows:
        a = tr.select_one("a.kt-ch-title")
        if not a:
            continue
        href = a["href"]         # например "/@foo" или "/joinchat/XYZ"
        path = href.lstrip("/")  # убираем начальный слэш
        result.append(path)
    return result


def parse_channel(username, headers):
    # Если приватный канал через joinchat/, то URL = BASE_URL/joinchat/…
    if username.startswith("joinchat/"):
        url = f"{BASE_URL}/{username}"
    else:
        # для обычных каналов убираем @ и вставляем в /@… 
        uname = username.lstrip("@")
        url = f"{BASE_URL}/@{uname}"

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    a_user      = soup.select_one("a.kt-widget__username")
    title       = a_user.get_text(strip=True)
    tg_link     = a_user["href"]
    tg_username = tg_link.rsplit("/", 1)[-1]
    if not tg_username.startswith("@"):
        tg_username = "@"+tg_username

    desc_block = soup.select_one("div.kt-widget__desc.t_long")
    desc_lines = []
    admins     = []
    if desc_block:
        for node in desc_block.children:
            if getattr(node, "name", None) == "br":
                continue
            text = node.get_text(strip=True) if hasattr(node, "get_text") else str(node).strip()
            link = node.get("href") if getattr(node, "name", None) == "a" else None
            if text:
                desc_lines.append((text, link))
                low = text.lower()
                if "админ" in low or "менеджер" in low:
                    admins.append((text, link))

    sub_span    = soup.select_one("span.kt-number.kt-font-brand[data-num=participants]")
    subscribers = sub_span.get_text(strip=True) if sub_span else "N/A"

    return {
        "title":       title,
        "tg_link":     tg_link,
        "tg_username": tg_username,
        "subscribers": subscribers,
        "description": desc_lines,
        "admins":      admins or None
    } 