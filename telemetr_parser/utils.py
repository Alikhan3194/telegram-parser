import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlencode, urlparse
from dataclasses import dataclass
import re
from typing import List, Optional

try:
    # Попытка относительного импорта (когда запускаем из telemetr_parser/)
    from config import BASE_URL, LIMITS_URL
except ImportError:
    # Абсолютный импорт (когда запускаем из корня проекта)
    from telemetr_parser.config import BASE_URL, LIMITS_URL


# Регулярные выражения для извлечения админов
ADMIN_KEYWORDS_RE = re.compile(
    r"(?:\badmin\b|\badministrator\b|\bmanager\b|\bcontact\b|\badvert\b|\bpromo\b|"
    r"\bреклам[аеи]\b|\bменеджер\b|\bменеджмент\b|\bсвязь\b|\bконтакт[ы]?\b|\bадмин\b)",
    flags=re.IGNORECASE
)

HANDLE_RE = re.compile(r"@([A-Za-z0-9_]{4,})")
TME_LINK_RE = re.compile(r"https?://t\.me/(?:joinchat/)?[A-Za-z0-9_/\-]+", flags=re.IGNORECASE)


def _normalize_handle_to_link(handle: str) -> str:
    """Конвертирует @handle в полную t.me ссылку."""
    handle = handle.lstrip("@").strip()
    return f"https://t.me/{handle}"


def _try_handle_from_link(link: str) -> str | None:
    """Пытается извлечь username из t.me ссылки."""
    try:
        p = urlparse(link)
        # /username или /joinchat/<code> или /s/<username>/...
        parts = [x for x in p.path.split("/") if x]
        if not parts:
            return None
        # Пробуем вытащить «обычный» username
        if parts[0].lower() in ("joinchat", "s"):
            # joinchat/s — username может идти дальше, но зачастую это инвайт/код; возвращаем None
            return None
        return parts[0]
    except Exception:
        return None


def extract_admins_from_text(about: str) -> list[tuple[str, str]]:
    """
    Извлекает админов по строкам описания. Ищет строки, где есть ADMIN_KEYWORDS_RE.
    В такой строке:
      — собирает все t.me ссылки;
      — собирает все @handles;
      — для @handle строит полноценную ссылку;
      — для t.me пытается извлечь handle; если не получается, в качестве «handle_or_label»
        кладём 't.me' или короткий текст без мусора.
    Возвращает список кортежей (handle_or_label, url). Дубликаты по url удаляются.
    """
    if not about:
        return []

    results: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    # Нормализуем переносы/неразрывные пробелы/эмодзи не мешают
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in about.splitlines() if ln.strip()]
    for ln in lines:
        if not ADMIN_KEYWORDS_RE.search(ln):
            continue

        # 1) t.me-ссылки
        for link in TME_LINK_RE.findall(ln):
            url = link.strip()
            if url not in seen_urls:
                handle = _try_handle_from_link(url)
                handle_or_label = f"@{handle}" if handle else "t.me"
                results.append((handle_or_label, url))
                seen_urls.add(url)

        # 2) @handles
        for h in HANDLE_RE.findall(ln):
            url = _normalize_handle_to_link(h)
            if url not in seen_urls:
                results.append((f"@{h}", url))
                seen_urls.add(url)

    return results


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

    # Устанавливаем обязательные параметры по умолчанию
    params = {
        # Обязательные
        "order_column":       order_column or "participants_count",
        "order_direction":    order_direction or "DESC",
        "lang_ru":            1 if lang_ru is None else lang_ru,
        "lang_uz":            0 if lang_uz is None else lang_uz,
        "channel_type":       channel_type or "all",
        "moderate":           moderate or "all",
        "verified":           verified or "all",
        "detailed_bot_added": detailed_bot_added or "all",
        # Остальные фильтры
        "links":              "\r\n".join(links) if links else None,
        "title":              title,
        "about":              about,
        "participants_from":  participants_from,
        "participants_to":    participants_to,
        "views_post_from":    views_post_from,
        "views_post_to":      views_post_to,
        "er_from":            er_from,
        "er_to":              er_to,
        "mentions_week_from": mentions_week_from,
        "mentions_week_to":   mentions_week_to,
        "sex_m_from":         sex_m_from,
        "sex_w_from":         sex_w_from,
        "lang_code":          lang_code,
        # Пагинация
        "page":               page,
    }

    clean = {k: v for k, v in params.items() if v not in (None, "")}
    return base + ("?" + urlencode(clean, doseq=True) if clean else "")


def fetch_listing(url, headers):
    """Простой GET: URL уже содержит все параметры (включая page).
    Ничего не дописывает к URL."""
    r = requests.get(url, headers=headers, timeout=20)
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


def parse_channel_html(username, headers):
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
    about_html_text = ""
    if desc_block:
        # Собираем весь текст для извлечения админов
        about_html_text = desc_block.get_text(" ", strip=True)
        
        # Для description сохраняем старую логику построчного разбора
        for node in desc_block.children:
            if getattr(node, "name", None) == "br":
                continue
            text = node.get_text(strip=True) if hasattr(node, "get_text") else str(node).strip()
            link = node.get("href") if getattr(node, "name", None) == "a" else None
            if text:
                desc_lines.append((text, link))

    # Используем новую логику извлечения админов из всего текста описания
    admins = extract_admins_from_text(about_html_text)

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


def _split_description_lines(text: str) -> List[str]:
    if not text:
        return []
    # Разделители: перенос строки, маркеры, вертикальные черты
    raw = [p.strip() for p in re.split(r"[\n\r\u2022\-\•\|]+", text) if p.strip()]
    return raw


def _extract_links(line: str) -> List[str]:
    urls = re.findall(r"https?://\S+", line)
    tme = re.findall(r"t\.me/\S+", line)
    return urls + tme


def _extract_handles(line: str) -> List[str]:
    return re.findall(r"@[A-Za-z0-9_]+", line)


def parse_channel_api(username_or_joinchat: str) -> dict:
    """Детальная карточка канала через официальный API.
    Fallback на HTML реализуется в вызывающем коде.
    """
    from .telemetr_api import get_channel_info, get_channel_subscribers
    # Нормализуем идентификатор
    cid = username_or_joinchat.strip()
    if not cid.startswith("joinchat/"):
        cid = cid.lstrip("@")
        cid = f"@{cid}" if not cid.startswith("@") else cid

    info = get_channel_info(cid)
    title = info.get("title") or info.get("name") or ""
    tg_link = info.get("link") or ""
    tg_username = info.get("username") or ("@" + (tg_link.rsplit("/", 1)[-1] if tg_link else ""))

    # Подписчики: берем participants_count, иначе добираем через /subscribers
    subscribers = info.get("participants_count")
    if not subscribers:
        try:
            subscribers = get_channel_subscribers(cid) or "N/A"
        except Exception:
            subscribers = "N/A"

    about_text = info.get("about") or ""
    
    # Используем новую логику извлечения админов
    admins = extract_admins_from_text(about_text)
    
    # Для description оставляем старую логику для совместимости
    lines = _split_description_lines(about_text)
    desc_lines: List[tuple[str, Optional[str]]] = []
    for line in lines:
        links = _extract_links(line)
        first_link = links[0] if links else None
        desc_lines.append((line, first_link))

    return {
        "title":       title,
        "tg_link":     tg_link,
        "tg_username": tg_username,
        "subscribers": subscribers,
        "description": desc_lines,
        "admins":      admins or None,
    }


@dataclass
class TelemetrLimit:
    name: str
    description: str
    current: int
    maximum: int
    severity: str = "warn"  # "gate" or "warn"


# Определяем какой лимит является критическим (gate)
GATE_LIMIT_NAME = "Лимит каналов"


def get_limits_from_html(headers) -> List[TelemetrLimit]:
    """Парсит профиль пользователя на telemetr.me и извлекает лимиты.

    Ищет блоки включая:
    - Лимит каналов (для ежедневного анализа) 
    - Количество аккаунтов
    - Количество устройств  
    - Запросов в API
    - Страниц в каталоге
    - Упоминания

    Ожидаем блоки вида:
      <div class="mb-3">
        <div class="float-right col-3">
          <div class="nowrap"><b>196</b> / 200</div>
        </div>
        <div class="sub-text">для ежедневного анализа</div>
      </div>

    Возвращает список TelemetrLimit с severity.
    """
    resp = requests.get(LIMITS_URL, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    limits: List[TelemetrLimit] = []
    for box in soup.select("div.mb-3"):
        desc_node = box.select_one("div.sub-text")
        value_node = box.select_one("div.float-right.col-3 div.nowrap")
        # Определяем название лимита — div без класса (или первый div, не относящийся к sub-text/float-right)
        name = None
        for child in box.find_all("div", recursive=False):
            classes = child.get("class", [])
            if "sub-text" in classes:
                continue
            if "float-right" in classes and "col-3" in classes:
                continue
            name = child.get_text(strip=True)
            if name:
                break

        if not value_node:
            continue
        desc = desc_node.get_text(strip=True) if desc_node else ""
        text = value_node.get_text(" ", strip=True)
        # Ожидаемый формат: "196 / 200" или "196/200"
        parts = text.replace(" ", "").split("/")
        if len(parts) != 2:
            continue
        try:
            current = int(parts[0].replace("\xa0", ""))
            maximum = int(parts[1].replace("\xa0", ""))
        except ValueError:
            continue
        
        # Определяем severity на основе имени лимита
        severity = "gate" if name == GATE_LIMIT_NAME else "warn"
        
        limits.append(TelemetrLimit(
            name=name or "", 
            description=desc, 
            current=current, 
            maximum=maximum,
            severity=severity
        ))

    return limits


def get_limits_from_api(headers) -> List[TelemetrLimit]:
    """Заглушка для будущей интеграции официального API Telemetr.
    Оставляем совместимый интерфейс с get_limits_from_html.
    """
    raise NotImplementedError("Telemetr official API integration not implemented yet")