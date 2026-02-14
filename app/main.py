"""
Flask web application for movie search and browsing
"""
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Movie, Offer, Rating, Genre, Actor, Director, Base
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/movies.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def get_session():
    """Get database session"""
    return Session()


@app.route('/')
def index():
    """Home page"""
    session = get_session()
    
    # Get some statistics
    total_movies = session.query(Movie).count()
    total_offers = session.query(Offer).count()
    
    # Get popular movies (sorted by rating and votes) with eager loading
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func, case
    
    # Get movies with average rating and total votes
    # Prioritize movies with both high ratings and many votes
    movies_with_ratings = session.query(
        Movie,
        func.avg(Rating.rating).label('avg_rating'),
        func.sum(Rating.votes_count).label('total_votes')
    ).outerjoin(Movie.ratings).group_by(Movie.id)
    
    # Sort by: 1) movies with ratings first, 2) by votes count, 3) by rating
    popular_movies_query = movies_with_ratings.order_by(
        case(
            (func.count(Rating.id) > 0, 1),
            else_=0
        ).desc(),
        func.sum(Rating.votes_count).desc().nullslast(),
        func.avg(Rating.rating).desc().nullslast()
    ).limit(12)
    
    # Execute query and get results
    results = popular_movies_query.all()
    
    # Now load relationships for these movies
    movie_ids = [r[0].id for r in results]
    recent_movies = session.query(Movie).options(
        joinedload(Movie.ratings),
        joinedload(Movie.genres),
        joinedload(Movie.actors),
        joinedload(Movie.directors)
    ).filter(Movie.id.in_(movie_ids)).all()
    
    # Sort in memory to preserve the order
    id_to_movie = {m.id: m for m in recent_movies}
    recent_movies = [id_to_movie[mid] for mid in movie_ids if mid in id_to_movie]
    
    # Convert to dicts to avoid DetachedInstanceError
    movies_data = []
    for movie in recent_movies:
        avg_rating = None
        if movie.ratings:
            avg_rating = round(sum(r.rating for r in movie.ratings) / len(movie.ratings), 1)
        
        movies_data.append({
            'id': movie.id,
            'canonical_name': movie.canonical_name,
            'release_year': movie.release_year,
            'movie_type': movie.movie_type,
            'image_url': movie.image_url,
            'avg_rating': avg_rating
        })
    
    session.close()
    
    return render_template('index.html', 
                         total_movies=total_movies,
                         total_offers=total_offers,
                         recent_movies=movies_data)


@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '')
    movie_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    session = get_session()
    
    # Build query with eager loading
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func, case
    
    # Build base query with ratings for sorting
    movies_query = session.query(Movie).options(
        joinedload(Movie.ratings),
        joinedload(Movie.genres)
    )
    
    # Text search
    if query:
        search_filter = or_(
            Movie.canonical_name.ilike(f'%{query}%'),
            Movie.original_name.ilike(f'%{query}%'),
            Movie.description.ilike(f'%{query}%')
        )
        movies_query = movies_query.filter(search_filter)
    
    # Filter by genre
    if genre:
        movies_query = movies_query.join(Movie.genres).filter(Genre.name == genre)
    
    # Filter by year
    if year:
        try:
            year_int = int(year)
            movies_query = movies_query.filter(Movie.release_year == year_int)
        except ValueError:
            pass
    
    # Filter by type
    if movie_type:
        movies_query = movies_query.filter(Movie.movie_type == movie_type)
    
    # Count total
    total = movies_query.count()
    
    # Sort by popularity (votes count and rating) if no text search
    if not query:
        # Create a subquery with rating stats
        rating_stats = session.query(
            Rating.movie_id,
            func.sum(Rating.votes_count).label('total_votes'),
            func.avg(Rating.rating).label('avg_rating')
        ).group_by(Rating.movie_id).subquery()
        
        # Join with rating stats and sort
        movies_query = movies_query.outerjoin(
            rating_stats, Movie.id == rating_stats.c.movie_id
        ).order_by(
            rating_stats.c.total_votes.desc().nullslast(),
            rating_stats.c.avg_rating.desc().nullslast(),
            Movie.release_year.desc()
        )
    else:
        # For text search, keep relevance order (id desc)
        movies_query = movies_query.order_by(Movie.id.desc())
    
    # Paginate and convert to dicts
    movies_results = movies_query.offset((page - 1) * per_page).limit(per_page).all()
    
    movies_data = []
    for movie in movies_results:
        avg_rating = None
        if movie.ratings:
            avg_rating = round(sum(r.rating for r in movie.ratings) / len(movie.ratings), 1)
        
        movies_data.append({
            'id': movie.id,
            'canonical_name': movie.canonical_name,
            'release_year': movie.release_year,
            'movie_type': movie.movie_type,
            'image_url': movie.image_url,
            'avg_rating': avg_rating,
            'genres': [{'name': g.name} for g in movie.genres]
        })
    
    # Get available genres for filter
    all_genres = [{'name': g.name} for g in session.query(Genre).order_by(Genre.name).all()]
    
    session.close()
    
    return render_template('search.html',
                         movies=movies_data,
                         query=query,
                         genre=genre,
                         year=year,
                         movie_type=movie_type,
                         page=page,
                         per_page=per_page,
                         total=total,
                         all_genres=all_genres)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Movie detail page"""
    session = get_session()
    
    from sqlalchemy.orm import joinedload
    movie = session.query(Movie).options(
        joinedload(Movie.genres),
        joinedload(Movie.actors),
        joinedload(Movie.directors),
        joinedload(Movie.ratings),
        joinedload(Movie.offers)
    ).filter_by(id=movie_id).first()
    
    if not movie:
        session.close()
        return "Movie not found", 404
    
    # Convert to dict to avoid DetachedInstanceError
    movie_data = {
        'id': movie.id,
        'canonical_name': movie.canonical_name,
        'original_name': movie.original_name,
        'release_year': movie.release_year,
        'description': movie.description,
        'movie_type': movie.movie_type,
        'duration': movie.duration,
        'image_url': movie.image_url,
        'imdb_id': movie.imdb_id,
        'tmdb_id': movie.tmdb_id,
        'kinopoisk_id': movie.kinopoisk_id,
        'genres': [{'name': g.name} for g in movie.genres],
        'actors': [{'id': a.id, 'name': a.name} for a in movie.actors],
        'directors': [{'id': d.id, 'name': d.name} for d in movie.directors]
    }
    
    offers_data = [{
        'id': o.id,
        'website_name': o.website_name,
        'url': o.url,
        'price': o.price
    } for o in movie.offers]
    
    ratings_data = [{
        'source': r.source,
        'rating': r.rating,
        'votes_count': r.votes_count
    } for r in movie.ratings]
    
    session.close()
    
    return render_template('movie.html',
                         movie=movie_data,
                         offers=offers_data,
                         ratings=ratings_data)


@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    session = get_session()
    
    search_filter = or_(
        Movie.canonical_name.ilike(f'%{query}%'),
        Movie.original_name.ilike(f'%{query}%')
    )
    
    movies = session.query(Movie).filter(search_filter).limit(limit).all()
    
    result = []
    for movie in movies:
        result.append({
            'id': movie.id,
            'name': movie.canonical_name,
            'year': movie.release_year,
            'type': movie.movie_type,
            'image_url': movie.image_url
        })
    
    session.close()
    
    return jsonify(result)


@app.route('/api/movie/<int:movie_id>')
def api_movie_detail(movie_id):
    """API endpoint for movie details"""
    session = get_session()
    
    movie = session.query(Movie).filter_by(id=movie_id).first()
    
    if not movie:
        session.close()
        return jsonify({'error': 'Movie not found'}), 404
    
    offers = session.query(Offer).filter_by(movie_id=movie_id).all()
    ratings = session.query(Rating).filter_by(movie_id=movie_id).all()
    
    result = {
        'id': movie.id,
        'canonical_name': movie.canonical_name,
        'original_name': movie.original_name,
        'release_year': movie.release_year,
        'description': movie.description,
        'movie_type': movie.movie_type,
        'duration': movie.duration,
        'image_url': movie.image_url,
        'genres': [g.name for g in movie.genres],
        'actors': [{'id': a.id, 'name': a.name} for a in movie.actors],
        'directors': [{'id': d.id, 'name': d.name} for d in movie.directors],
        'offers': [{
            'website': o.website_name,
            'url': o.url,
            'price': o.price
        } for o in offers],
        'ratings': [{
            'source': r.source,
            'rating': r.rating,
            'votes': r.votes_count
        } for r in ratings]
    }
    
    session.close()
    
    return jsonify(result)


@app.template_filter('rating_color')
def rating_color(rating):
    """Get color class for rating"""
    if not rating:
        return ''
    if rating >= 8:
        return 'success'
    elif rating >= 6:
        return 'warning'
    else:
        return 'danger'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
