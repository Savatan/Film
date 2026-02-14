"""
TMDb (The Movie Database) Parser
Uses official API for reliable data collection
"""
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

class TMDbParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        
    def discover_movies(self, page: int = 1, year: Optional[int] = None) -> Dict:
        """Discover movies with filters"""
        url = f"{self.base_url}/discover/movie"
        params = {
            "api_key": self.api_key,
            "page": page,
            "sort_by": "popularity.desc",
            "include_adult": False,
            "language": "ru-RU"
        }
        if year:
            params["year"] = year
            
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def discover_tv_shows(self, page: int = 1, year: Optional[int] = None) -> Dict:
        """Discover TV shows with filters"""
        url = f"{self.base_url}/discover/tv"
        params = {
            "api_key": self.api_key,
            "page": page,
            "sort_by": "popularity.desc",
            "include_adult": False,
            "language": "ru-RU"
        }
        if year:
            params["first_air_date_year"] = year
            
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed information about a movie"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "append_to_response": "credits,external_ids"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_tv_details(self, tv_id: int) -> Dict:
        """Get detailed information about a TV show"""
        url = f"{self.base_url}/tv/{tv_id}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "append_to_response": "credits,external_ids"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def parse_movie_data(self, movie_data: Dict) -> Dict:
        """Parse movie data into unified format"""
        credits = movie_data.get('credits', {})
        external_ids = movie_data.get('external_ids', {})
        
        return {
            'source': 'tmdb',
            'tmdb_id': movie_data.get('id'),
            'imdb_id': external_ids.get('imdb_id'),
            'canonical_name': movie_data.get('title'),
            'original_name': movie_data.get('original_title'),
            'release_year': int(movie_data.get('release_date', '0000')[:4]) if movie_data.get('release_date') else None,
            'release_date': movie_data.get('release_date'),
            'description': movie_data.get('overview'),
            'movie_type': 'movie',
            'duration': movie_data.get('runtime'),
            'image_url': f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None,
            'rating': movie_data.get('vote_average'),
            'votes_count': movie_data.get('vote_count'),
            'genres': [g['name'] for g in movie_data.get('genres', [])],
            'actors': [{'name': actor['name'], 'imdb_id': None} for actor in credits.get('cast', [])[:10]],
            'directors': [{'name': crew['name'], 'imdb_id': None} for crew in credits.get('crew', []) if crew.get('job') == 'Director'],
            'url': f"https://www.themoviedb.org/movie/{movie_data.get('id')}",
            'raw_data': json.dumps(movie_data)
        }
    
    def parse_tv_data(self, tv_data: Dict) -> Dict:
        """Parse TV show data into unified format"""
        credits = tv_data.get('credits', {})
        external_ids = tv_data.get('external_ids', {})
        
        return {
            'source': 'tmdb',
            'tmdb_id': tv_data.get('id'),
            'imdb_id': external_ids.get('imdb_id'),
            'canonical_name': tv_data.get('name'),
            'original_name': tv_data.get('original_name'),
            'release_year': int(tv_data.get('first_air_date', '0000')[:4]) if tv_data.get('first_air_date') else None,
            'release_date': tv_data.get('first_air_date'),
            'description': tv_data.get('overview'),
            'movie_type': 'series',
            'duration': tv_data.get('episode_run_time', [None])[0],
            'image_url': f"https://image.tmdb.org/t/p/w500{tv_data.get('poster_path')}" if tv_data.get('poster_path') else None,
            'rating': tv_data.get('vote_average'),
            'votes_count': tv_data.get('vote_count'),
            'genres': [g['name'] for g in tv_data.get('genres', [])],
            'actors': [{'name': actor['name'], 'imdb_id': None} for actor in credits.get('cast', [])[:10]],
            'directors': [{'name': crew['name'], 'imdb_id': None} for crew in credits.get('crew', []) if crew.get('job') == 'Director'][:5],
            'url': f"https://www.themoviedb.org/tv/{tv_data.get('id')}",
            'raw_data': json.dumps(tv_data)
        }
    
    def collect_data(self, num_items: int = 1000, include_tv: bool = True) -> List[Dict]:
        """Collect movie and TV show data"""
        results = []
        movies_to_collect = num_items // 2 if include_tv else num_items
        tv_to_collect = num_items // 2 if include_tv else 0
        
        print(f"Collecting {movies_to_collect} movies from TMDb...")
        page = 1
        while len([r for r in results if r['movie_type'] == 'movie']) < movies_to_collect:
            try:
                data = self.discover_movies(page=page)
                for movie in data.get('results', []):
                    try:
                        time.sleep(0.25)  # Rate limiting
                        details = self.get_movie_details(movie['id'])
                        parsed = self.parse_movie_data(details)
                        results.append(parsed)
                        print(f"Collected movie: {parsed['canonical_name']} ({parsed['release_year']})")
                        
                        if len([r for r in results if r['movie_type'] == 'movie']) >= movies_to_collect:
                            break
                    except Exception as e:
                        print(f"Error processing movie {movie.get('id')}: {e}")
                        continue
                
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        if include_tv:
            print(f"\nCollecting {tv_to_collect} TV shows from TMDb...")
            page = 1
            while len([r for r in results if r['movie_type'] == 'series']) < tv_to_collect:
                try:
                    data = self.discover_tv_shows(page=page)
                    for tv in data.get('results', []):
                        try:
                            time.sleep(0.25)
                            details = self.get_tv_details(tv['id'])
                            parsed = self.parse_tv_data(details)
                            results.append(parsed)
                            print(f"Collected TV show: {parsed['canonical_name']} ({parsed['release_year']})")
                            
                            if len([r for r in results if r['movie_type'] == 'series']) >= tv_to_collect:
                                break
                        except Exception as e:
                            print(f"Error processing TV show {tv.get('id')}: {e}")
                            continue
                    
                    page += 1
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error fetching TV page {page}: {e}")
                    break
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(data)} items to {filename}")


if __name__ == "__main__":
    # Example usage
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("Please set TMDB_API_KEY in .env file")
        exit(1)
    
    parser = TMDbParser(api_key)
    data = parser.collect_data(num_items=1000, include_tv=True)
    parser.save_to_json(data, 'data/tmdb_data.json')
