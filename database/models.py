"""
Database models for the movies integration project
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Date, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Many-to-many relationship tables
movie_genres = Table('movie_genres', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

movie_actors = Table('movie_actors', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('actor_id', Integer, ForeignKey('actors.id'), primary_key=True)
)

movie_directors = Table('movie_directors', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id'), primary_key=True),
    Column('director_id', Integer, ForeignKey('directors.id'), primary_key=True)
)


class Movie(Base):
    """Main table for unified movies/series"""
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    canonical_name = Column(String(500), nullable=False, index=True)
    original_name = Column(String(500))
    release_year = Column(Integer, index=True)
    release_date = Column(Date)
    description = Column(Text)
    movie_type = Column(String(50))  # 'movie', 'series', 'documentary', etc.
    duration = Column(Integer)  # in minutes
    image_url = Column(String(1000))
    imdb_id = Column(String(50), unique=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    kinopoisk_id = Column(Integer, unique=True, index=True)
    
    # Relationships
    offers = relationship('Offer', back_populates='movie', cascade='all, delete-orphan')
    ratings = relationship('Rating', back_populates='movie', cascade='all, delete-orphan')
    genres = relationship('Genre', secondary=movie_genres, back_populates='movies')
    actors = relationship('Actor', secondary=movie_actors, back_populates='movies')
    directors = relationship('Director', secondary=movie_directors, back_populates='movies')
    
    def __repr__(self):
        return f"<Movie(id={self.id}, name='{self.canonical_name}', year={self.release_year})>"


class Offer(Base):
    """Specific offers/listings from different websites"""
    __tablename__ = 'offers'
    
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False, index=True)
    website_name = Column(String(100), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    title = Column(String(500))
    price = Column(Float)  # if applicable (for rent/purchase)
    date_parsed = Column(Date, default=datetime.utcnow)
    raw_data = Column(Text)  # JSON string with all original data
    
    # Relationship
    movie = relationship('Movie', back_populates='offers')
    
    def __repr__(self):
        return f"<Offer(id={self.id}, website='{self.website_name}', movie_id={self.movie_id})>"


class Rating(Base):
    """Ratings from different sources"""
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # 'imdb', 'tmdb', 'kinopoisk'
    rating = Column(Float)
    votes_count = Column(Integer)
    
    # Relationship
    movie = relationship('Movie', back_populates='ratings')
    
    def __repr__(self):
        return f"<Rating(movie_id={self.movie_id}, source='{self.source}', rating={self.rating})>"


class Genre(Base):
    """Movie genres"""
    __tablename__ = 'genres'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationship
    movies = relationship('Movie', secondary=movie_genres, back_populates='genres')
    
    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Actor(Base):
    """Actors/Actresses"""
    __tablename__ = 'actors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    imdb_id = Column(String(50), unique=True)
    
    # Relationship
    movies = relationship('Movie', secondary=movie_actors, back_populates='actors')
    
    def __repr__(self):
        return f"<Actor(id={self.id}, name='{self.name}')>"


class Director(Base):
    """Directors"""
    __tablename__ = 'directors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    imdb_id = Column(String(50), unique=True)
    
    # Relationship
    movies = relationship('Movie', secondary=movie_directors, back_populates='directors')
    
    def __repr__(self):
        return f"<Director(id={self.id}, name='{self.name}')>"


def create_database(database_url):
    """Create database and all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()
