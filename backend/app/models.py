from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Title(Base):
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    canonical_title = Column(String, index=True)
    original_title = Column(String, index=True)
    year = Column(Integer, index=True)
    type = Column(String, index=True)  # movie / tv
    description = Column(Text)
    poster_url = Column(String)
    rating_global = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    offers = relationship("Offer", back_populates="title")
    attributes = relationship("TitleAttribute", back_populates="title")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("titles.id"))
    website_name = Column(String, index=True)
    website_internal_id = Column(String, index=True)
    rating_site = Column(Float)
    url = Column(String)
    date_parsed = Column(DateTime, default=datetime.utcnow)

    title = relationship("Title", back_populates="offers")


class TitleAttribute(Base):
    __tablename__ = "title_attributes"

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("titles.id"))
    attribute_name = Column(String, index=True)
    attribute_value = Column(String)

    title = relationship("Title", back_populates="attributes")


class RawOffer(Base):
    __tablename__ = "raw_offers"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True)
    raw_title = Column(String)
    raw_original_title = Column(String)
    raw_year = Column(Integer)
    raw_type = Column(String)
    raw_description = Column(Text)
    raw_rating = Column(Float)
    raw_genres = Column(Text)  # JSON-строка
    raw_countries = Column(Text)  # JSON-строка
    url = Column(String)
    date_parsed = Column(DateTime, default=datetime.utcnow)
