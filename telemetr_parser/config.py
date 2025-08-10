# telemetr_parser/config.py
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://telemetr.me/",
    "Cookie": "_ym_uid=175280336883121087; _ym_d=1752803368; _ym_isad=2; _ym_visorc=w; PHPSESSID=ekec56mekvcnhl7rduqbdvj8on",
}

BASE_URL = "https://telemetr.me" 
LIMITS_URL = f"{BASE_URL}/profile"

# Telemetr official API configuration
import os
TELEMETR_API_BASE = "https://api.telemetr.me"
TELEMETR_API_TOKEN = os.getenv("erySdBXrEPe87pArC4HJdyZZyxIxGLschh9eZhOL1ni8msF9YBsyDWJ2OMDKsq8DxUNFAyJQxV52B") or ""
API_HEADERS = {
    "Authorization": f"Bearer {TELEMETR_API_TOKEN}",
    "Accept": "application/json",
}