#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     Сбор полных данных (1000+ фильмов с каждого источника)    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Activate venv
source venv/bin/activate

# Check API keys
if grep -q "YOUR_TMDB_API_KEY_HERE" .env; then
    echo "❌ Ошибка: TMDb API ключ не настроен!"
    echo ""
    echo "Получите ключ:"
    echo "1. Регистрация: https://www.themoviedb.org/signup"
    echo "2. API ключ: https://www.themoviedb.org/settings/api"
    echo "3. Отредактируйте .env и добавьте ключ"
    echo ""
    echo "Команда: nano .env"
    exit 1
fi

echo "🚀 Начинаем сбор данных..."
echo "⏱️  Это займёт 45-60 минут"
echo ""

# Step 1: Parse TMDb
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Шаг 1/4: Парсинг TMDb (1000 записей)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python parsers/tmdb_parser.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при парсинге TMDb"
    exit 1
fi

# Step 2: Parse IMDb
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Шаг 2/4: Парсинг IMDb (1000 записей)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python parsers/imdb_parser.py
if [ $? -ne 0 ]; then
    echo "❌ Ошибка при парсинге IMDb"
    exit 1
fi

# Step 3: Parse OMDb (if API key is set)
echo ""
if [ -n "$(grep OMDB_API_KEY .env | grep -v '^#' | grep -v 'YOUR_' | grep -v '^OMDB_API_KEY=$')" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📡 Шаг 3/4: Парсинг OMDb (1000 записей)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python parsers/omdb_parser.py
    if [ $? -ne 0 ]; then
        echo "⚠️  Ошибка при парсинге OMDb (пропускаем)"
    fi
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏭️  Шаг 3/4: Пропуск OMDb (нет API ключа)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Получите ключ: http://www.omdbapi.com/apikey.aspx"
fi

# Step 4: Integrate into database
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  Шаг 4/4: Интеграция в базу данных"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
rm -f data/movies.db
python scripts/deduplicate_fixed.py

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ ГОТОВО! База данных создана                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Запустите приложение:"
echo "  python app/main.py"
echo ""
echo "Откройте: http://localhost:8000"
