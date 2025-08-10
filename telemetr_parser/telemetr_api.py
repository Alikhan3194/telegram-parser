import time
import requests

class TelemetrApiError(Exception):
    pass

from .config import TELEMETR_API_BASE, API_HEADERS, TELEMETR_API_TOKEN


def _ensure_token():
    if not TELEMETR_API_TOKEN:
        raise TelemetrApiError(
            "Не задан TELEMETR_API_TOKEN (получите на https://telemetr.me/profile/)."
        )


def _get(path: str, params: dict) -> dict:
    _ensure_token()
    url = f"{TELEMETR_API_BASE}{path}"
    for i in range(3):
        r = requests.get(url, headers=API_HEADERS, params=params, timeout=20)
        if r.status_code == 429:
            time.sleep(1.5 * (i + 1))
            continue
        if not r.ok:
            raise TelemetrApiError(f"API {path} {r.status_code}: {r.text[:200]}")
        data = r.json()
        if data.get("status") != "ok":
            raise TelemetrApiError(f"Непредвиденный ответ API {path}: {data}")
        return data["response"]
    raise TelemetrApiError("Превышено число попыток обращения к API")


def get_channel_info(channel_id: str) -> dict:
    """Получить детальную информацию о канале по API.
    channel_id: "@username" | "joinchat/XXXX" | peer id
    """
    return _get("/channels/get", {"channelId": channel_id})


def get_channel_subscribers(channel_id: str, group: str = "day") -> int | None:
    """Получить последнюю точку по подписчикам (группа day/week/month)."""
    resp = _get("/channels/subscribers", {"channelId": channel_id, "group": group})
    if isinstance(resp, list) and resp:
        last = resp[-1]
        for k in ("count", "value", "subscribers"):
            if k in last and isinstance(last[k], (int, float)):
                return int(last[k])
    return None


