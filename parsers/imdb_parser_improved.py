"""
Improved IMDb Parser - собирает больше данных
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional


class IMDbParserImproved:
    def __init__(self):
        self.base_url = "https://www.imdb.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8'
        })
    
    def generate_movie_ids(self, start_num: int = 133093, count: int = 1000) -> List[str]:
        """Generate IMDb IDs based on known patterns"""
        # IMDb IDs обычно идут последовательно: tt0133093 (The Matrix)
        # Мы возьмём популярный диапазон ID
        ids = []
        
        # Популярные фильмы обычно в диапазоне tt0000001 - tt9999999
        # Начнём с tt0100000 (фильмы 90-х и позже)
        popular_ranges = [
            (100000, 200000),  # 90-е годы
            (200000, 500000),  # 2000-е
            (500000, 1000000), # 2010-е
            (1000000, 2000000), # 2010-2015
            (5000000, 6000000), # 2015-2020
            (10000000, 12000000), # 2020+
        ]
        
        import random
        for start, end in popular_ranges:
            # Случайно выбираем ID из каждого диапазона
            range_count = count // len(popular_ranges)
            for _ in range(range_count):
                num = random.randint(start, end)
                ids.append(f"tt{num:07d}")
        
        return ids[:count]
    
    def get_chart_ids(self, chart_url: str, limit: int = 100) -> List[str]:
        """Get IDs from any IMDb chart page"""
        try:
            response = self.session.get(chart_url)
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
        except Exception as e:
            print(f"Error fetching chart {chart_url}: {e}")
            return []
    
    def get_title_details(self, imdb_id: str) -> Optional[Dict]:
        """Get detailed information about a title"""
        url = f"{self.base_url}/title/{imdb_id}/"
        
        try:
            response = self.session.get(url, timeout=10)
            
            # Проверяем что страница существует
            if response.status_code == 404:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find JSON-LD data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                data = json.loads(json_ld.string)
                return self._parse_json_ld(data, imdb_id, url)
            
            return None
            
        except Exception as e:
            return None
    
    def _parse_json_ld(self, data: Dict, imdb_id: str, url: str) -> Dict:
        """Parse JSON-LD structured data"""
        movie_type = 'series' if data.get('@type') in ['TVSeries', 'TVMiniSeries'] else 'movie'
        
        date_published = data.get('datePublished', '')
        release_year = int(date_published[:4]) if date_published and len(date_published) >= 4 else None
        
        duration = None
        if 'duration' in data:
            duration_str = data['duration']
            match = re.search(r'PT(\d+)M', duration_str)
            if match:
                duration = int(match.group(1))
        
        actors = []
        if 'actor' in data:
            actor_list = data['actor'] if isinstance(data['actor'], list) else [data['actor']]
            actors = [{'name': a.get('name'), 'imdb_id': None} for a in actor_list if isinstance(a, dict)][:10]
        
        directors = []
        if 'director' in data:
            director_list = data['director'] if isinstance(data['director'], list) else [data['director']]
            directors = [{'name': d.get('name'), 'imdb_id': None} for d in director_list if isinstance(d, dict)]
        
        genres = data.get('genre', [])
        if isinstance(genres, str):
            genres = [genres]
        
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
    
    def collect_data(self, num_items: int = 1000) -> List[Dict]:
        """Collect movie data from IMDb"""
        results = []
        
        # Step 1: Get IDs from charts (гарантированно существующие)
        print("Collecting IDs from IMDb charts...")
        chart_ids = []
        
        charts = [
            ('https://www.imdb.com/chart/top/', 250),
            ('https://www.imdb.com/chart/moviemeter/', 100),
            ('https://www.imdb.com/chart/tvmeter/', 100),
        ]
        
        for chart_url, limit in charts:
            ids = self.get_chart_ids(chart_url, limit)
            chart_ids.extend(ids)
            print(f"  Found {len(ids)} IDs from {chart_url}")
            time.sleep(2)
        
        chart_ids = list(set(chart_ids))
        print(f"Total chart IDs: {len(chart_ids)}")
        
        # Step 2: Generate additional IDs
        if len(chart_ids) < num_items:
            print(f"\nGenerating additional {num_items - len(chart_ids)} random IDs...")
            additional_ids = self.generate_movie_ids(count=num_items - len(chart_ids))
            all_ids = chart_ids + additional_ids
        else:
            all_ids = chart_ids[:num_items]
        
        print(f"\nFetching details for {len(all_ids)} titles...")
        print("(Some IDs may not exist - this is normal)")
        
        # Step 3: Fetch details
        for idx, imdb_id in enumerate(all_ids, 1):
            try:
                details = self.get_title_details(imdb_id)
                if details:
                    results.append(details)
                    print(f"[{len(results)}/{num_items}] ✓ {details['canonical_name']} ({details['release_year']})")
                    
                    if len(results) >= num_items:
                        break
                
                # Rate limiting
                time.sleep(0.5 if idx % 10 == 0 else 0.3)
                
                # Progress update
                if idx % 50 == 0:
                    print(f"  Progress: {idx}/{len(all_ids)} checked, {len(results)} collected")
                
            except Exception as e:
                continue
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved {len(data)} items to {filename}")


if __name__ == "__main__":
    parser = IMDbParserImproved()
    data = parser.collect_data(num_items=1000)
    parser.save_to_json(data, 'data/imdb_data.json')
