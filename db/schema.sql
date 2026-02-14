CREATE TABLE IF NOT EXISTS titles (
    id SERIAL PRIMARY KEY,
    canonical_title VARCHAR(512),
    original_title VARCHAR(512),
    year INT,
    type VARCHAR(32),
    description TEXT,
    poster_url TEXT,
    rating_global REAL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    title_id INT REFERENCES titles(id) ON DELETE CASCADE,
    website_name VARCHAR(64),
    website_internal_id VARCHAR(128),
    rating_site REAL,
    url TEXT,
    date_parsed TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS title_attributes (
    id SERIAL PRIMARY KEY,
    title_id INT REFERENCES titles(id) ON DELETE CASCADE,
    attribute_name VARCHAR(128),
    attribute_value VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS raw_offers (
    id SERIAL PRIMARY KEY,
    source VARCHAR(64),
    raw_title VARCHAR(512),
    raw_original_title VARCHAR(512),
    raw_year INT,
    raw_type VARCHAR(32),
    raw_description TEXT,
    raw_rating REAL,
    raw_genres TEXT,
    raw_countries TEXT,
    url TEXT,
    date_parsed TIMESTAMP DEFAULT NOW()
);
