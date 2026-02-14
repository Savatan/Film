#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Movie Database - Quick Start Script                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists and has API key
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file with your API keys."
    echo "See .env.example for template."
    exit 1
fi

# Check if TMDB_API_KEY is set
if grep -q "YOUR_TMDB_API_KEY_HERE" .env; then
    echo "⚠️  TMDB_API_KEY not configured!"
    echo "Please edit .env file and add your TMDb API key."
    echo "Get it from: https://www.themoviedb.org/settings/api"
    echo ""
    echo "Would you like to run with SAMPLE DATA for demo? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "📦 Creating sample data..."
        python scripts/create_sample_data.py
        echo ""
        echo "🗄️  Creating database from sample data..."
        python scripts/deduplicate_fixed.py
    else
        exit 1
    fi
else
    echo "🚀 Starting full data collection..."
    echo "This will take 45-60 minutes..."
    echo ""
    
    # Run parsers
    echo "📡 Step 1/4: Parsing TMDb..."
    python parsers/tmdb_parser.py
    
    echo ""
    echo "📡 Step 2/4: Parsing IMDb..."
    python parsers/imdb_parser.py
    
    echo ""
    if [ -n "$(grep KINOPOISK_API_KEY .env | grep -v '^#' | grep -v 'YOUR_')" ]; then
        echo "📡 Step 3/4: Parsing Kinopoisk..."
        python parsers/kinopoisk_parser.py
    else
        echo "⏭️  Step 3/4: Skipping Kinopoisk (no API key)"
    fi
    
    echo ""
    echo "🗄️  Step 4/4: Integrating data into database..."
    python scripts/deduplicate_fixed.py
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ DATABASE READY!                                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Starting web application..."
echo "📍 Open browser: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask app
python app/main.py
