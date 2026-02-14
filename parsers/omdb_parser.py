"""
OMDb API Parser - альтернатива Kinopoisk
Получите бесплатный ключ: http://www.omdbapi.com/apikey.aspx
"""
import requests
import json
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class OMDbParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
        self.session = requests.Session()
    
    def search_movies(self, query: str, year: Optional[int] = None, page: int = 1) -> Dict:
        """Search movies by title"""
        params = {
            'apikey': self.api_key,
            's': query,
            'type': 'movie',
            'page': page
        }
        if year:
            params['y'] = year
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_movie_details(self, imdb_id: str) -> Dict:
        """Get detailed movie info by IMDb ID"""
        params = {
            'apikey': self.api_key,
            'i': imdb_id,
            'plot': 'full'
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def parse_movie_data(self, movie_data: Dict) -> Dict:
        """Parse OMDb data into unified format"""
        if movie_data.get('Response') == 'False':
            return None
        
        # Parse year
        year_str = movie_data.get('Year', '').split('–')[0]  # Handle ranges like "2020–2023"
        try:
            release_year = int(year_str) if year_str and year_str.isdigit() else None
        except:
            release_year = None
        
        # Parse runtime
        runtime_str = movie_data.get('Runtime', '').replace(' min', '')
        try:
            duration = int(runtime_str) if runtime_str != 'N/A' else None
        except:
            duration = None
        
        # Parse rating
        imdb_rating = movie_data.get('imdbRating')
        try:
            rating = float(imdb_rating) if imdb_rating and imdb_rating != 'N/A' else None
        except:
            rating = None
        
        # Parse votes
        imdb_votes = movie_data.get('imdbVotes', '').replace(',', '')
        try:
            votes_count = int(imdb_votes) if imdb_votes and imdb_votes != 'N/A' else None
        except:
            votes_count = None
        
        # Parse genres
        genres_str = movie_data.get('Genre', '')
        genres = [g.strip() for g in genres_str.split(',')] if genres_str != 'N/A' else []
        
        # Parse actors
        actors_str = movie_data.get('Actors', '')
        actors = [{'name': a.strip(), 'imdb_id': None} for a in actors_str.split(',')] if actors_str != 'N/A' else []
        
        # Parse directors
        directors_str = movie_data.get('Director', '')
        directors = [{'name': d.strip(), 'imdb_id': None} for d in directors_str.split(',')] if directors_str != 'N/A' else []
        
        # Determine type
        movie_type = 'series' if movie_data.get('Type') == 'series' else 'movie'
        
        return {
            'source': 'omdb',
            'imdb_id': movie_data.get('imdbID'),
            'tmdb_id': None,
            'kinopoisk_id': None,
            'canonical_name': movie_data.get('Title'),
            'original_name': movie_data.get('Title'),
            'release_year': release_year,
            'release_date': movie_data.get('Released') if movie_data.get('Released') != 'N/A' else None,
            'description': movie_data.get('Plot') if movie_data.get('Plot') != 'N/A' else None,
            'movie_type': movie_type,
            'duration': duration,
            'image_url': movie_data.get('Poster') if movie_data.get('Poster') != 'N/A' else None,
            'rating': rating,
            'votes_count': votes_count,
            'genres': genres,
            'actors': actors[:10],
            'directors': directors,
            'url': f"https://www.imdb.com/title/{movie_data.get('imdbID')}/",
            'raw_data': json.dumps(movie_data)
        }
    
    def collect_data(self, num_items: int = 1000) -> List[Dict]:
        """Collect movie data"""
        results = []
        
        # Popular search terms to get variety of movies
        search_terms = [
            'love', 'war', 'the', 'man', 'life', 'last', 'dark', 'dead', 'star',
            'night', 'day', 'king', 'american', 'legend', 'story', 'world',
            'return', 'future', 'lost', 'game', 'final', 'first', 'new', 'old',
            'big', 'little', 'good', 'bad', 'beautiful', 'secret', 'mystery'
        ]
        
        print(f"Collecting {num_items} movies from OMDb...")
        print("Using various search terms to get diverse results...\n")
        
        seen_ids = set()
        
        for term in search_terms:
            if len(results) >= num_items:
                break
            
            print(f"Searching: '{term}'...")
            
            # Search multiple pages for each term
            for page in range(1, 11):  # Up to 10 pages per term
                try:
                    search_results = self.search_movies(term, page=page)
                    
                    if search_results.get('Response') == 'False':
                        break
                    
                    movies = search_results.get('Search', [])
                    if not movies:
                        break
                    
                    for movie in movies:
                        imdb_id = movie.get('imdbID')
                        if imdb_id in seen_ids:
                            continue
                        
                        seen_ids.add(imdb_id)
                        
                        try:
                            # Get full details
                            details = self.get_movie_details(imdb_id)
                            parsed = self.parse_movie_data(details)
                            
                            if parsed:
                                results.append(parsed)
                                print(f"  [{len(results)}/{num_items}] ✓ {parsed['canonical_name']} ({parsed['release_year']})")
                                
                                if len(results) >= num_items:
                                    break
                            
                            time.sleep(0.1)  # Rate limiting
                            
                        except Exception as e:
                            print(f"  Error processing {imdb_id}: {e}")
                            continue
                    
                    if len(results) >= num_items:
                        break
                    
                    time.sleep(0.5)  # Rate limiting between pages
                    
                except Exception as e:
                    print(f"  Error searching '{term}' page {page}: {e}")
                    break
            
            if len(results) >= num_items:
                break
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save collected data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved {len(data)} items to {filename}")


if __name__ == "__main__":
    api_key = os.getenv('OMDB_API_KEY')
    
    if not api_key:
        print("❌ OMDb API key not found!")
        print("\n📝 Get a FREE key:")
        print("1. Go to: http://www.omdbapi.com/apikey.aspx")
        print("2. Select FREE tier (1,000 requests/day)")
        print("3. Enter your email and verify")
        print("4. Add key to .env file: OMDB_API_KEY=your_key")
        exit(1)
    
    parser = OMDbParser(api_key)
    data = parser.collect_data(num_items=1000)
    parser.save_to_json(data, 'data/omdb_data.json')
