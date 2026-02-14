#!/bin/bash

echo "=== Movie Database Integration Project ==="
echo "Running complete pipeline..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in API keys"
    exit 1
fi

# Source environment variables
source .env

# Check API keys
if [ -z "$TMDB_API_KEY" ]; then
    echo "Warning: TMDB_API_KEY not set in .env"
fi

echo "Step 1: Parsing TMDb..."
python parsers/tmdb_parser.py
echo ""

echo "Step 2: Parsing IMDb..."
python parsers/imdb_parser.py
echo ""

if [ ! -z "$KINOPOISK_API_KEY" ]; then
    echo "Step 3: Parsing Kinopoisk..."
    python parsers/kinopoisk_parser.py
    echo ""
else
    echo "Step 3: Skipping Kinopoisk (no API key)"
    echo ""
fi

echo "Step 4: Integrating data into database..."
python scripts/deduplicate.py
echo ""

echo "Step 5: Starting web application..."
echo "Application will be available at http://localhost:5000"
python app/main.py
