"""
Create sample data for quick testing without running full parsers
"""
import json
import os

# Sample movie data
sample_movies = [
    {
        'source': 'tmdb',
        'tmdb_id': 603,
        'imdb_id': 'tt0133093',
        'canonical_name': 'The Matrix',
        'original_name': 'The Matrix',
        'release_year': 1999,
        'release_date': '1999-03-30',
        'description': 'Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.',
        'movie_type': 'movie',
        'duration': 136,
        'image_url': 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
        'rating': 8.2,
        'votes_count': 24000,
        'genres': ['Action', 'Science Fiction'],
        'actors': [
            {'name': 'Keanu Reeves', 'imdb_id': None},
            {'name': 'Laurence Fishburne', 'imdb_id': None},
            {'name': 'Carrie-Anne Moss', 'imdb_id': None}
        ],
        'directors': [{'name': 'Lana Wachowski', 'imdb_id': None}, {'name': 'Lilly Wachowski', 'imdb_id': None}],
        'url': 'https://www.themoviedb.org/movie/603',
        'raw_data': '{}'
    },
    {
        'source': 'tmdb',
        'tmdb_id': 238,
        'imdb_id': 'tt0068646',
        'canonical_name': 'The Godfather',
        'original_name': 'The Godfather',
        'release_year': 1972,
        'release_date': '1972-03-14',
        'description': 'Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family.',
        'movie_type': 'movie',
        'duration': 175,
        'image_url': 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg',
        'rating': 8.7,
        'votes_count': 18000,
        'genres': ['Drama', 'Crime'],
        'actors': [
            {'name': 'Marlon Brando', 'imdb_id': None},
            {'name': 'Al Pacino', 'imdb_id': None},
            {'name': 'James Caan', 'imdb_id': None}
        ],
        'directors': [{'name': 'Francis Ford Coppola', 'imdb_id': None}],
        'url': 'https://www.themoviedb.org/movie/238',
        'raw_data': '{}'
    },
    {
        'source': 'tmdb',
        'tmdb_id': 550,
        'imdb_id': 'tt0137523',
        'canonical_name': 'Fight Club',
        'original_name': 'Fight Club',
        'release_year': 1999,
        'release_date': '1999-10-15',
        'description': 'A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.',
        'movie_type': 'movie',
        'duration': 139,
        'image_url': 'https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
        'rating': 8.4,
        'votes_count': 26000,
        'genres': ['Drama'],
        'actors': [
            {'name': 'Brad Pitt', 'imdb_id': None},
            {'name': 'Edward Norton', 'imdb_id': None},
            {'name': 'Helena Bonham Carter', 'imdb_id': None}
        ],
        'directors': [{'name': 'David Fincher', 'imdb_id': None}],
        'url': 'https://www.themoviedb.org/movie/550',
        'raw_data': '{}'
    }
]

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Save sample data
with open('data/tmdb_data.json', 'w', encoding='utf-8') as f:
    json.dump(sample_movies, f, ensure_ascii=False, indent=2)

print(f"✅ Created sample data with {len(sample_movies)} movies")
print("📁 Saved to: data/tmdb_data.json")
print("\nNext steps:")
print("1. Run: python scripts/deduplicate.py")
print("2. Run: python app/main.py")
print("3. Open: http://localhost:5000")
