import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://telemetr.me/",
    "Cookie": "_ym_uid=175280336883121087; _ym_d=1752803368; _ym_isad=2; _ym_visorc=w; PHPSESSID=ekec56mekvcnhl7rduqbdvj8on",
}

URL = "https://telemetr.me/channels/"

def get_categories():
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"Ошибка запроса: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    category_elements = soup.select("div.col-md-12.text-justify span.cat-group a")

    categories = [el.get_text(strip=True) for el in category_elements]
    return categories

if __name__ == "__main__":
    categories = get_categories()
    print("Категории:")
    for cat in categories:
        print("-", cat)
