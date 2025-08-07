import requests

# 1) Собираем заголовки из инспектора браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://tgstat.ru/",
    # возьмите отсюда все cookie из вкладки Network→Cookies→Request Cookies
    "Cookie": "_gid=GA1.2.1743350330.1752816584; _ym_uid=1752816584863445944; _ym_d=1752816584; _ym_isad=2; tgstat_sirk=amhl0dup0ikm70570kck6ejqj0; tgstat_idrk=067e4fa68e57fbb8112af4d47fb7358bc4f9a337815a52b7465d5f52f51bb829a%3A2%3A%7Bi%3A0%3Bs%3A11%3A%22tgstat_idrk%22%3Bi%3A1%3Bs%3A53%3A%22%5B11901746%2C%22JcnhcCPq2C8fqigw-q4g_DmaOTKzFK70%22%2C2592000%5D%22%3B%7D; _tgstat_csrk=a1a9092a515133b164230e757ffae3d3a4c0502f1d633d601d5e507a7aab0868a%3A2%3A%7Bi%3A0%3Bs%3A12%3A%22_tgstat_csrk%22%3Bi%3A1%3Bs%3A32%3A%22WJrh4diRWbjgvSQaVEtxUBPeFi60B9yE%22%3B%7D; tgstat_settings=5b69ff99a7bb78728aef97fd0ba1759d3fc86fc69275d98da53b00488072fccba%3A2%3A%7Bi%3A0%3Bs%3A15%3A%22tgstat_settings%22%3Bi%3A1%3Bs%3A19%3A%22%7B%22fp%22%3A%22ipc_Lsw1-j%22%7D%22%3B%7D; _gat_gtag_UA_104082833_1=1; _ga_ZEKJ7V8PH3=GS2.1.s1752816583$o1$g1$t1752816884$j60$l0$h0; _ga=GA1.1.1118149690.1752816584"
}

URL = "https://tgstat.ru/channels/search"

def fetch_search_page():
    resp = requests.get(URL, headers=HEADERS)
    resp.raise_for_status()  # если статус ≠200, выбросит ошибку
    return resp.text

if __name__ == "__main__":
    html = fetch_search_page()
    print(html)  # выведет весь HTML в терминал