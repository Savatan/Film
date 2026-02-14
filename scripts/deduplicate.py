
import json
from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Movie, Offer, Rating, Genre, Actor, Director, create_database, get_session


class DataIntegrator:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.genre_cache = {}
        self.actor_cache = {}
        self.director_cache = {}
    
    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison"""
        if not s:
            return ""
        return s.lower().strip().replace(":", "").replace("-", " ")
    
    def find_duplicate(self, movie_data: Dict) -> Optional[Movie]:
        """Find if movie already exists in database"""
        # Strategy 1: Match by external IDs (most reliable)
        if movie_data.get('imdb_id'):
            existing = self.session.query(Movie).filter_by(
                imdb_id=movie_data['imdb_id']
            ).first()
            if existing:
                return existing
        
        if movie_data.get('tmdb_id'):
            existing = self.session.query(Movie).filter_by(
                tmdb_id=movie_data['tmdb_id']
            ).first()
            if existing:
                return existing
        
        if movie_data.get('kinopoisk_id'):
            existing = self.session.query(Movie).filter_by(
                kinopoisk_id=movie_data['kinopoisk_id']
            ).first()
            if existing:
                return existing
        
        # Strategy 2: Fuzzy match by name and year
        if movie_data.get('canonical_name') and movie_data.get('release_year'):
            candidates = self.session.query(Movie).filter_by(
                release_year=movie_data['release_year']
            ).all()
            
            normalized_name = self.normalize_string(movie_data['canonical_name'])
            
            for candidate in candidates:
                candidate_name = self.normalize_string(candidate.canonical_name)
                similarity = fuzz.ratio(normalized_name, candidate_name)
                
                # High similarity threshold
                if similarity >= 90:
                    return candidate
        
        return None
    
    def get_or_create_genre(self, genre_name: str) -> Genre:
        """Get or create genre"""
        if genre_name in self.genre_cache:
            return self.genre_cache[genre_name]
        
        genre = self.session.query(Genre).filter_by(name=genre_name).first()
        if not genre:
            genre = Genre(name=genre_name)
            self.session.add(genre)
            self.session.flush()
        
        self.genre_cache[genre_name] = genre
        return genre
    
    def get_or_create_actor(self, actor_data: Dict) -> Actor:
        """Get or create actor"""
        actor_name = actor_data.get('name')
        if not actor_name:
            return None
        
        if actor_name in self.actor_cache:
            return self.actor_cache[actor_name]
        
        actor = self.session.query(Actor).filter_by(name=actor_name).first()
        if not actor:
            actor = Actor(
                name=actor_name,
                imdb_id=actor_data.get('imdb_id')
            )
            self.session.add(actor)
            self.session.flush()
        
        self.actor_cache[actor_name] = actor
        return actor
    
    def get_or_create_director(self, director_data: Dict) -> Director:
        """Get or create director"""
        director_name = director_data.get('name')
        if not director_name:
            return None
        
        if director_name in self.director_cache:
            return self.director_cache[director_name]
        
        director = self.session.query(Director).filter_by(name=director_name).first()
        if not director:
            director = Director(
                name=director_name,
                imdb_id=director_data.get('imdb_id')
            )
            self.session.add(director)
            self.session.flush()
        
        self.director_cache[director_name] = director
        return director
    
    def merge_movie_data(self, existing: Movie, new_data: Dict) -> Movie:
        """Merge new data into existing movie record"""
        # Update fields if they are empty or new data is better
        if new_data.get('imdb_id') and not existing.imdb_id:
            existing.imdb_id = new_data['imdb_id']
        
        if new_data.get('tmdb_id') and not existing.tmdb_id:
            existing.tmdb_id = new_data['tmdb_id']
        
        if new_data.get('kinopoisk_id') and not existing.kinopoisk_id:
            existing.kinopoisk_id = new_data['kinopoisk_id']
        
        if new_data.get('description') and not existing.description:
            existing.description = new_data['description']
        
        if new_data.get('image_url') and not existing.image_url:
            existing.image_url = new_data['image_url']
        
        if new_data.get('duration') and not existing.duration:
            existing.duration = new_data['duration']
        
        if new_data.get('original_name') and not existing.original_name:
            existing.original_name = new_data['original_name']
        
        # Add genres
        for genre_name in new_data.get('genres', []):
            genre = self.get_or_create_genre(genre_name)
            if genre not in existing.genres:
                existing.genres.append(genre)
        
        # Add actors
        for actor_data in new_data.get('actors', []):
            actor = self.get_or_create_actor(actor_data)
            if actor and actor not in existing.actors:
                existing.actors.append(actor)
        
        # Add directors
        for director_data in new_data.get('directors', []):
            director = self.get_or_create_director(director_data)
            if director and director not in existing.directors:
                existing.directors.append(director)
        
        return existing
    
    def create_movie(self, movie_data: Dict) -> Movie:
        """Create new movie record"""
        movie = Movie(
            canonical_name=movie_data.get('canonical_name'),
            original_name=movie_data.get('original_name'),
            release_year=movie_data.get('release_year'),
            release_date=movie_data.get('release_date'),
            description=movie_data.get('description'),
            movie_type=movie_data.get('movie_type'),
            duration=movie_data.get('duration'),
            image_url=movie_data.get('image_url'),
            imdb_id=movie_data.get('imdb_id'),
            tmdb_id=movie_data.get('tmdb_id'),
            kinopoisk_id=movie_data.get('kinopoisk_id')
        )
        
        # Add genres
        for genre_name in movie_data.get('genres', []):
            genre = self.get_or_create_genre(genre_name)
            movie.genres.append(genre)
        
        # Add actors
        for actor_data in movie_data.get('actors', []):
            actor = self.get_or_create_actor(actor_data)
            if actor:
                movie.actors.append(actor)
        
        # Add directors
        for director_data in movie_data.get('directors', []):
            director = self.get_or_create_director(director_data)
            if director:
                movie.directors.append(director)
        
        self.session.add(movie)
        self.session.flush()
        
        return movie
    
    def integrate_data(self, data_files: List[str]):
        """Integrate data from multiple sources"""
        total_processed = 0
        total_new = 0
        total_merged = 0
        total_offers = 0
        
        for data_file in data_files:
            print(f"\nProcessing {data_file}...")
            
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for idx, movie_data in enumerate(data, 1):
                    try:
                        # Check if movie exists
                        existing_movie = self.find_duplicate(movie_data)
                        
                        if existing_movie:
                            # Merge data
                            movie = self.merge_movie_data(existing_movie, movie_data)
                            total_merged += 1
                            action = "merged"
                        else:
                            # Create new
                            movie = self.create_movie(movie_data)
                            total_new += 1
                            action = "created"
                        
                        # Create offer
                        offer = Offer(
                            movie_id=movie.id,
                            website_name=movie_data.get('source'),
                            url=movie_data.get('url'),
                            title=movie_data.get('canonical_name'),
                            price=movie_data.get('price'),
                            raw_data=movie_data.get('raw_data')
                        )
                        self.session.add(offer)
                        total_offers += 1
                        
                        # Create rating if available
                        if movie_data.get('rating'):
                            # Check if rating from this source already exists
                            existing_rating = self.session.query(Rating).filter_by(
                                movie_id=movie.id,
                                source=movie_data.get('source')
                            ).first()
                            
                            if not existing_rating:
                                rating = Rating(
                                    movie_id=movie.id,
                                    source=movie_data.get('source'),
                                    rating=movie_data.get('rating'),
                                    votes_count=movie_data.get('votes_count')
                                )
                                self.session.add(rating)
                        
                        total_processed += 1
                        
                        if idx % 100 == 0:
                            print(f"  Processed {idx}/{len(data)} items...")
                            self.session.commit()
                    
                    except Exception as e:
                        print(f"  Error processing item {idx}: {e}")
                        self.session.rollback()
                        continue
                
                # Final commit for this file
                self.session.commit()
                print(f"  Completed {data_file}: {len(data)} items")
                
            except Exception as e:
                print(f"  Error loading {data_file}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Integration Summary:")
        print(f"  Total items processed: {total_processed}")
        print(f"  New movies created: {total_new}")
        print(f"  Existing movies merged: {total_merged}")
        print(f"  Total offers created: {total_offers}")
        print(f"  Total unique movies: {self.session.query(Movie).count()}")
        print(f"{'='*60}")


def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    # Database URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/movies.db')
    
    # Create database
    print("Creating database...")
    engine = create_database(database_url)
    session = get_session(engine)
    
    # Data files to integrate
    data_files = [
        'data/tmdb_data.json',
        'data/imdb_data.json',
        'data/kinopoisk_data.json'
    ]
    
    # Filter existing files
    existing_files = [f for f in data_files if os.path.exists(f)]
    
    if not existing_files:
        print("No data files found! Please run parsers first.")
        return
    
    print(f"Found {len(existing_files)} data files to integrate")
    
    # Integrate data
    integrator = DataIntegrator(session)
    integrator.integrate_data(existing_files)
    
    # Close session
    session.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
