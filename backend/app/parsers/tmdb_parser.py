import json
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.themoviedb.org"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_popular_movies(pages: int = 10) -> List[Dict]:
    """Пример парсинга популярных фильмов с TMDB (HTML-страницы).
    Для реального использования желательно подключать официальный API.
    """
    items: List[Dict] = []

    for page in range(1, pages + 1):
        url = f"{BASE_URL}/movie?page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select("section div.card")
        for card in cards:
            title_el = card.select_one("h2 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url_rel = title_el.get("href") or ""
            url_full = BASE_URL + url_rel

            year = None
            year_el = card.select_one("p.release_date")
            if year_el:
                text = year_el.get_text(strip=True)
                if text:
                    try:
                        year = int(text[:4])
                    except ValueError:
                        pass

            rating = None
            rating_el = card.select_one("span.user_score_chart")
            if rating_el and rating_el.get("data-percent"):
                try:
                    rating = float(rating_el["data-percent"]) / 10.0
                except ValueError:
                    pass

            items.append(
                {
                    "title": title,
                    "original_title": None,
                    "year": year,
                    "type": "movie",
                    "description": None,
                    "rating": rating,
                    "genres": [],
                    "countries": [],
                    "url": url_full,
                }
            )

    return items


if __name__ == "__main__":
    data = parse_popular_movies(pages=20)
    with open("data/tmdb.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
