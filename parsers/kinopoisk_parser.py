"""
Kinopoisk Parser
Note: Kinopoisk requires authentication for official API. This uses web scraping.
Consider using unofficial API: https://kinopoiskapiunofficial.tech/
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional


class KinopoiskParser:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://www.kinopoisk.ru"
        self.api_base_url = "https://kinopoiskapiunofficial.tech/api"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
        })
        
        if api_key:
            self.session.headers.update({'X-API-KEY': api_key})
    
    def get_top_films_via_api(self, page: int = 1) -> Dict:
        """Get top films using unofficial API"""
        if not self.api_key:
            raise ValueError("API key required for this method")
        
        url = f"{self.api_base_url}/v2.2/films/top"
        params = {
            'type': 'TOP_250_BEST_FILMS',
            'page': page
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_film_details_via_api(self, film_id: int) -> Dict:
        """Get film details using unofficial API"""
        if not self.api_key:
            raise ValueError("API key required for this method")
        
        url = f"{self.api_base_url}/v2.2/films/{film_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def search_films_via_api(self, keyword: str = "", page: int = 1, year: Optional[int] = None) -> Dict:
        """Search films using unofficial API"""
        if not self.api_key:
            raise ValueError("API key required for this method")
        
        url = f"{self.api_base_url}/v2.1/films/search-by-keyword"
        params = {
            'keyword': keyword,
            'page': page
        }
        if year:
            params['yearFrom'] = year
            params['yearTo'] = year
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_staff_via_api(self, film_id: int) -> List[Dict]:
        """Get film staff (actors, directors) using unofficial API"""
        if not self.api_key:
            raise ValueError("API key required for this method")
        
        url = f"{self.api_base_url}/v1/staff"
        params = {'filmId': film_id}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def parse_film_data_from_api(self, film_data: Dict, staff_data: List[Dict] = None) -> Dict:
        """Parse film data from API into unified format"""
        # Determine type
        movie_type = 'movie'
        if film_data.get('type') in ['TV_SERIES', 'MINI_SERIES']:
            movie_type = 'series'
        
        # Extract year
        release_year = film_data.get('year')
        
        # Extract IMDb ID if available
        imdb_id = film_data.get('imdbId')
        
        # Process staff data
        actors = []
        directors = []
        if staff_data:
            for person in staff_data:
                if person.get('professionKey') == 'ACTOR':
                    actors.append({
                        'name': person.get('nameRu') or person.get('nameEn'),
                        'imdb_id': None
                    })
                elif person.get('professionKey') == 'DIRECTOR':
                    directors.append({
                        'name': person.get('nameRu') or person.get('nameEn'),
                        'imdb_id': None
                    })
        
        # Limit actors and directors
        actors = actors[:10]
        directors = directors[:5]
        
        return {
            'source': 'kinopoisk',
            'kinopoisk_id': film_data.get('kinopoiskId') or film_data.get('filmId'),
            'imdb_id': imdb_id,
            'tmdb_id': None,
            'canonical_name': film_data.get('nameRu') or film_data.get('nameOriginal'),
            'original_name': film_data.get('nameOriginal') or film_data.get('nameRu'),
            'release_year': release_year,
            'release_date': None,
            'description': film_data.get('description') or film_data.get('shortDescription'),
            'movie_type': movie_type,
            'duration': film_data.get('filmLength'),
            'image_url': film_data.get('posterUrl') or film_data.get('posterUrlPreview'),
            'rating': film_data.get('ratingKinopoisk'),
            'votes_count': film_data.get('ratingKinopoiskVoteCount'),
            'genres': [g.get('genre') for g in film_data.get('genres', [])],
            'actors': actors,
            'directors': directors,
            'url': f"https://www.kinopoisk.ru/film/{film_data.get('kinopoiskId') or film_data.get('filmId')}/",
            'raw_data': json.dumps(film_data)
        }
    
    def collect_data_via_api(self, num_items: int = 1000, include_tv: bool = True) -> List[Dict]:
        """Collect data using unofficial API"""
        if not self.api_key:
            print("Warning: No API key provided. Limited functionality.")
            return []
        
        results = []
        movies_to_collect = num_items // 2 if include_tv else num_items
        tv_to_collect = num_items // 2 if include_tv else 0
        
        print(f"Collecting top films from Kinopoisk API...")
        
        # Collect top films
        page = 1
        while len(results) < movies_to_collect:
            try:
                data = self.get_top_films_via_api(page=page)
                films = data.get('films', [])
                
                if not films:
                    break
                
                for film in films:
                    try:
                        film_id = film.get('filmId')
                        time.sleep(0.2)  # Rate limiting
                        
                        # Get detailed info
                        details = self.get_film_details_via_api(film_id)
                        
                        # Get staff info
                        time.sleep(0.2)
                        staff = self.get_staff_via_api(film_id)
                        
                        parsed = self.parse_film_data_from_api(details, staff)
                        results.append(parsed)
                        print(f"Collected: {parsed['canonical_name']} ({parsed['release_year']})")
                        
                        if len(results) >= movies_to_collect:
                            break
                        
                    except Exception as e:
                        print(f"Error processing film {film_id}: {e}")
                        continue
                
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        # For TV series, we'd need to use search or different endpoints
        # This is simplified for the example
        if include_tv and len(results) < num_items:
            print(f"\nSearching for TV series...")
            try:
                # Search for popular series
                search_result = self.search_films_via_api(keyword="сериал", page=1)
                for film in search_result.get('films', [])[:tv_to_collect]:
                    try:
                        film_id = film.get('filmId')
                        time.sleep(0.2)
                        
                        details = self.get_film_details_via_api(film_id)
                        if details.get('type') in ['TV_SERIES', 'MINI_SERIES']:
                            time.sleep(0.2)
                            staff = self.get_staff_via_api(film_id)
                            parsed = self.parse_film_data_from_api(details, staff)
                            results.append(parsed)
                            print(f"Collected TV series: {parsed['canonical_name']} ({parsed['release_year']})")
                        
                        if len(results) >= num_items:
                            break
                            
                    except Exception as e:
                        print(f"Error processing series: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error searching TV series: {e}")
        
        return results
    
    def collect_data_fallback(self, num_items: int = 100) -> List[Dict]:
        """Fallback method without API - very limited"""
        print("Warning: Using fallback scraping method. Data will be limited.")
        print("Consider getting an API key from https://kinopoiskapiunofficial.tech/")
        
        # This is a placeholder - actual implementation would require 
        # more sophisticated scraping
        results = []
        
        # Could scrape from public lists, but Kinopoisk has strong anti-scraping
        # Best to use the API
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(data)} items to {filename}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('KINOPOISK_API_KEY')
    
    parser = KinopoiskParser(api_key=api_key)
    
    if api_key:
        data = parser.collect_data_via_api(num_items=1000, include_tv=True)
    else:
        print("No Kinopoisk API key found. Using fallback method.")
        data = parser.collect_data_fallback(num_items=100)
    
    parser.save_to_json(data, 'data/kinopoisk_data.json')
