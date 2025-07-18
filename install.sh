#!/bin/bash

# URI XML Search - Django Backend Installation Script

echo "🚀 URI XML Search - Django Backend Installation"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create migrations
echo "🗄️ Creating database migrations..."
python manage.py makemigrations search_app

# Run migrations
echo "🏗️ Running database migrations..."
python manage.py migrate

# Ask if user wants to create superuser
echo ""
read -p "❓ Do you want to create a superuser account? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser
fi

# Ask if user wants to index XML files
echo ""
read -p "❓ Do you want to index XML files from URI web archives? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Starting XML indexing (this may take a while)..."
    echo "⏳ Indexing first 5 files for testing..."
    python manage.py index_xml --max-files 5 --delay 2.0 --clear
    
    echo ""
    read -p "❓ Index all files? This will take longer (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Indexing all XML files..."
        python manage.py index_xml --clear --delay 1.0
    fi
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the development server: python manage.py runserver"
echo "2. Test the API: curl 'http://127.0.0.1:8000/search/?q=history'"
echo "3. Access admin interface: http://127.0.0.1:8000/admin/"
echo "4. Install the WordPress plugin for the frontend"
echo ""
echo "📖 For full documentation, see README.md"
echo ""
echo "🔧 To activate the virtual environment in the future:"
echo "   source venv/bin/activate"
