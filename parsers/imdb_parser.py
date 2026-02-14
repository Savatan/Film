
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class IMDbParser:
    def __init__(self, use_selenium: bool = False):
        self.base_url = "https://www.imdb.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8'
        })
        self.use_selenium = use_selenium
        self.driver = None
        
        if use_selenium:
            self._init_selenium()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def get_top_movies(self, limit: int = 250) -> List[str]:
        """Get IMDb IDs from top 250 movies list"""
        url = f"{self.base_url}/chart/top/"
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        movie_ids = []
        # Find all movie links
        links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
        
        for link in links:
            href = link.get('href')
            match = re.search(r'(tt\d+)', href)
            if match and match.group(1) not in movie_ids:
                movie_ids.append(match.group(1))
                if len(movie_ids) >= limit:
                    break
        
        return movie_ids
    
    def get_popular_movies(self, limit: int = 100) -> List[str]:
        """Get IMDb IDs from popular movies"""
        url = f"{self.base_url}/chart/moviemeter/"
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        movie_ids = []
        links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
        
        for link in links:
            href = link.get('href')
            match = re.search(r'(tt\d+)', href)
            if match and match.group(1) not in movie_ids:
                movie_ids.append(match.group(1))
                if len(movie_ids) >= limit:
                    break
        
        return movie_ids
    
    def get_popular_tv_shows(self, limit: int = 100) -> List[str]:
        """Get IMDb IDs from popular TV shows"""
        url = f"{self.base_url}/chart/tvmeter/"
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tv_ids = []
        links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
        
        for link in links:
            href = link.get('href')
            match = re.search(r'(tt\d+)', href)
            if match and match.group(1) not in tv_ids:
                tv_ids.append(match.group(1))
                if len(tv_ids) >= limit:
                    break
        
        return tv_ids
    
    def get_title_details(self, imdb_id: str) -> Optional[Dict]:
        """Get detailed information about a title"""
        url = f"{self.base_url}/title/{imdb_id}/"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find JSON-LD data (most reliable)
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                data = json.loads(json_ld.string)
                return self._parse_json_ld(data, imdb_id, url)
            
            # Fallback to HTML parsing
            return self._parse_html(soup, imdb_id, url)
            
        except Exception as e:
            print(f"Error fetching {imdb_id}: {e}")
            return None
    
    def _parse_json_ld(self, data: Dict, imdb_id: str, url: str) -> Dict:
        """Parse JSON-LD structured data"""
        movie_type = 'series' if data.get('@type') in ['TVSeries', 'TVMiniSeries'] else 'movie'
        
        # Extract year from datePublished
        date_published = data.get('datePublished', '')
        release_year = int(date_published[:4]) if date_published and len(date_published) >= 4 else None
        
        # Extract duration
        duration = None
        if 'duration' in data:
            duration_str = data['duration']
            # Parse ISO 8601 duration (e.g., "PT142M")
            match = re.search(r'PT(\d+)M', duration_str)
            if match:
                duration = int(match.group(1))
        
        # Extract actors and directors
        actors = []
        if 'actor' in data:
            actor_list = data['actor'] if isinstance(data['actor'], list) else [data['actor']]
            actors = [{'name': a.get('name'), 'imdb_id': None} for a in actor_list if isinstance(a, dict)]
        
        directors = []
        if 'director' in data:
            director_list = data['director'] if isinstance(data['director'], list) else [data['director']]
            directors = [{'name': d.get('name'), 'imdb_id': None} for d in director_list if isinstance(d, dict)]
        
        # Extract genres
        genres = data.get('genre', [])
        if isinstance(genres, str):
            genres = [genres]
        
        # Extract rating
        rating = None
        votes_count = None
        if 'aggregateRating' in data:
            rating_data = data['aggregateRating']
            rating = float(rating_data.get('ratingValue', 0))
            votes_count = int(rating_data.get('ratingCount', 0))
        
        return {
            'source': 'imdb',
            'imdb_id': imdb_id,
            'tmdb_id': None,
            'canonical_name': data.get('name'),
            'original_name': data.get('name'),
            'release_year': release_year,
            'release_date': date_published,
            'description': data.get('description'),
            'movie_type': movie_type,
            'duration': duration,
            'image_url': data.get('image'),
            'rating': rating,
            'votes_count': votes_count,
            'genres': genres,
            'actors': actors,
            'directors': directors,
            'url': url,
            'raw_data': json.dumps(data)
        }
    
    def _parse_html(self, soup: BeautifulSoup, imdb_id: str, url: str) -> Dict:
        """Fallback HTML parsing method"""
        # This is a simplified version - IMDb's HTML structure changes frequently
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else "Unknown"
        
        return {
            'source': 'imdb',
            'imdb_id': imdb_id,
            'tmdb_id': None,
            'canonical_name': title_text,
            'original_name': title_text,
            'release_year': None,
            'release_date': None,
            'description': None,
            'movie_type': 'movie',
            'duration': None,
            'image_url': None,
            'rating': None,
            'votes_count': None,
            'genres': [],
            'actors': [],
            'directors': [],
            'url': url,
            'raw_data': '{}'
        }
    
    def collect_data(self, num_items: int = 1000, include_tv: bool = True) -> List[Dict]:
        """Collect movie and TV show data from IMDb"""
        results = []
        movies_to_collect = num_items // 2 if include_tv else num_items
        tv_to_collect = num_items // 2 if include_tv else 0
        
        # Collect movie IDs
        print(f"Collecting movie IDs from IMDb...")
        movie_ids = []
        movie_ids.extend(self.get_top_movies(limit=250))
        time.sleep(2)
        movie_ids.extend(self.get_popular_movies(limit=movies_to_collect - len(movie_ids)))
        movie_ids = list(set(movie_ids))[:movies_to_collect]
        
        # Collect TV show IDs
        tv_ids = []
        if include_tv:
            print(f"Collecting TV show IDs from IMDb...")
            time.sleep(2)
            tv_ids = self.get_popular_tv_shows(limit=tv_to_collect)
            tv_ids = list(set(tv_ids))[:tv_to_collect]
        
        # Fetch details for all IDs
        all_ids = movie_ids + tv_ids
        print(f"\nFetching details for {len(all_ids)} titles...")
        
        for idx, imdb_id in enumerate(all_ids, 1):
            try:
                details = self.get_title_details(imdb_id)
                if details:
                    results.append(details)
                    print(f"[{idx}/{len(all_ids)}] Collected: {details['canonical_name']} ({details['release_year']})")
                
                # Rate limiting - be respectful to IMDb servers
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing {imdb_id}: {e}")
                continue
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(data)} items to {filename}")
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    parser = IMDbParser(use_selenium=False)
    data = parser.collect_data(num_items=1000, include_tv=True)
    parser.save_to_json(data, 'data/imdb_data.json')
