# URI XML Search System

A complete search solution for URI Special Collections XML archives, consisting of a Django backend API and WordPress frontend integration.

## Overview

This system allows users to search through hundreds of XML files from the URI web archives (`https://webarchives.apps.uri.edu/xml/`) via a user-friendly WordPress interface. The search results display formatted excerpts with direct links to the original XML files.

## Architecture

- **Backend**: Django REST API that indexes and searches XML files
- **Frontend**: WordPress plugin that provides search interface
- **Data Source**: URI web archives XML collection

## Installation

### Part 1: Django Backend Setup

#### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Git

#### Step 1: Clone and Setup the Django Project

```bash
# Clone the repository
git clone https://github.com/uri-libraries/uascsearch.git
cd uascsearch

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django djangorestframework django-cors-headers requests beautifulsoup4 django-extensions
```

#### Step 2: Configure Django Settings

Edit `uascsearch/settings.py` and update the `ALLOWED_HOSTS` for your deployment:

```python
# For production, add your domain
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'your-domain.com']

# Update CORS settings for your WordPress site
CORS_ALLOWED_ORIGINS = [
    "https://web.uri.edu",
    "https://your-wordpress-site.com",
]
```

#### Step 3: Database Setup

```bash
# Create database migrations
python manage.py makemigrations search_app
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser
```

#### Step 4: Index XML Files

```bash
# Test with a few files first
python manage.py index_xml --max-files 5 --delay 2.0 --clear

# Index all files (this may take a while - 283+ files)
python manage.py index_xml --clear --delay 1.0
```

#### Step 5: Start the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/search/`

#### Step 6: Test the API

```bash
# Test search functionality
curl "http://127.0.0.1:8000/search/?q=history"
```

### Part 2: WordPress Frontend Setup

#### Prerequisites
- WordPress site with admin access
- FTP/SFTP access or file manager

**Choose the appropriate WordPress integration based on your site's restrictions:**

#### Option A: Full JavaScript Plugin (Recommended)
For sites that allow JavaScript and custom plugins.

1. Create a new directory: `/wp-content/plugins/uri-xml-search/`
2. Upload these files from the `wordpress-integration/` folder:
   - `uri-xml-search.php`
   - `uri-xml-search.js`
   - `uri-xml-search.css`
   - `search-results-template.php`

#### Option B: PHP-Only Plugin (Locked-Down Sites)
For sites that restrict JavaScript but allow PHP plugins.

1. Create a new directory: `/wp-content/plugins/uri-xml-search-nojs/`
2. Upload these files from the `wordpress-integration/` folder:
   - `uri-xml-search-nojs.php`
   - `uri-xml-search-nojs.css`

#### Option C: Simple Link Plugin (Highly Restricted)
For sites that only allow basic shortcodes.

1. Create a new directory: `/wp-content/plugins/xml-search-link/`
2. Upload this file from the `wordpress-integration/` folder:
   - `xml-search-link.php`
3. Host the `standalone-search.html` file on your server

**For detailed WordPress installation instructions, see [`wordpress-integration/README.md`](wordpress-integration/README.md)**

#### General WordPress Setup Steps

1. Go to WordPress Admin → Plugins
2. Find "URI XML Search" and click "Activate"

#### Step 3: Configure the Plugin

1. Go to WordPress Admin → Settings → URI XML Search
2. Set the API Base URL:
   - For development: `http://127.0.0.1:8000`
   - For production: `https://your-django-domain.com`
3. Click "Save Changes"

#### Step 4: Add Search Box to Your Page

1. Edit the page where you want the search box (e.g., manuscripts list page)
2. Add this shortcode where you want the search box to appear:

```shortcode
[uri_xml_search placeholder="Search manuscripts and archives..." button_text="Search Archives"]
```

#### Step 5: Test the Integration

1. Visit the page with the search box
2. Enter a search term (e.g., "history", "college", "manuscripts")
3. Click "Search Archives"
4. You should be redirected to `/xml-search-results/` with formatted results

## Production Deployment

### Django Backend Deployment

#### Option 1: Using a VPS/Server

1. **Install Python and dependencies**:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

2. **Setup the application**:
```bash
# Clone to production directory
git clone https://github.com/uri-libraries/uascsearch.git /var/www/uascsearch
cd /var/www/uascsearch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure for production**:
```python
# In settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'web.uri.edu']

# Use a production database (PostgreSQL recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'uascsearch',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

4. **Setup static files and run migrations**:
```bash
python manage.py collectstatic
python manage.py migrate
```

5. **Configure Nginx and Gunicorn**:
```bash
# Install Gunicorn
pip install gunicorn

# Create Gunicorn service file
sudo nano /etc/systemd/system/uascsearch.service
```

Add this content:
```ini
[Unit]
Description=URI XML Search Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/uascsearch
Environment="PATH=/var/www/uascsearch/venv/bin"
ExecStart=/var/www/uascsearch/venv/bin/gunicorn --workers 3 --bind unix:/var/www/uascsearch/uascsearch.sock uascsearch.wsgi:application

[Install]
WantedBy=multi-user.target
```

6. **Configure Nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://unix:/var/www/uascsearch/uascsearch.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        root /var/www/uascsearch;
    }
}
```

#### Option 2: Using Docker

1. **Create Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

2. **Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: uascsearch
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

3. **Deploy**:
```bash
docker-compose up -d
```

### WordPress Production Configuration

1. **Update API URL**: Change the API URL in WordPress settings to your production Django URL
2. **Enable HTTPS**: Ensure both WordPress and Django are served over HTTPS
3. **Test thoroughly**: Verify search functionality works across different devices and browsers

## Usage

### Search Interface

Users can search the XML archives using the search box on your WordPress page. The search will:

1. Query the Django API for matching documents
2. Display results with:
   - Document filename (linked to original XML)
   - Content snippet
   - File size and modification date
   - Pagination for large result sets

### Search Features

- **Full-text search**: Searches within XML content
- **Filename search**: Also searches document filenames
- **Pagination**: Handles large result sets efficiently
- **Responsive design**: Works on all devices
- **Direct links**: Results link to original XML files

### API Endpoints

- `GET /search/?q=query&page=1&per_page=10` - Search XML documents
- `GET /admin/` - Django admin interface (requires authentication)

## Maintenance

### Regular Tasks

#### Re-index XML Files
```bash
# Update the index periodically to catch new files
python manage.py index_xml --clear --delay 1.0
```

#### Monitor Performance
```bash
# Check Django logs
tail -f /var/log/django/debug.log

# Monitor API response times
curl -w "@curl-format.txt" "http://your-api.com/search/?q=test"
```

#### Database Maintenance
```bash
# Backup database
python manage.py dumpdata > backup.json

# Clean up old search logs if implemented
python manage.py clearsessions
```

### Troubleshooting

#### Common Issues

1. **Search returns no results**
   - Check Django server is running: `curl http://your-api.com/search/?q=test`
   - Verify XML files are indexed: Check admin interface
   - Ensure CORS is configured for your WordPress domain

2. **WordPress shows 404 on results page**
   - Go to WordPress Admin → Settings → Permalinks
   - Click "Save Changes" to flush rewrite rules

3. **API connection errors**
   - Check Django `ALLOWED_HOSTS` setting
   - Verify firewall allows connections on port 8000
   - Check CORS configuration

4. **Slow search performance**
   - Consider adding database indexes
   - Implement caching (Redis/Memcached)
   - Optimize XML content extraction

#### Debug Mode

Enable debug mode in WordPress:
```php
// In wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
```

Check logs in `/wp-content/debug.log`

## Security Considerations

### Production Security

1. **Django Security**:
   - Set `DEBUG = False`
   - Use strong `SECRET_KEY`
   - Implement rate limiting
   - Use HTTPS only
   - Regular security updates

2. **WordPress Security**:
   - Keep WordPress and plugins updated
   - Use strong admin passwords
   - Implement security headers
   - Regular backups

3. **Server Security**:
   - Configure firewall
   - Use SSL certificates
   - Regular system updates
   - Monitor access logs

## Performance Optimization

### Django Optimization

1. **Database Optimization**:
   - Add indexes on frequently searched fields
   - Use database connection pooling
   - Consider read replicas for heavy loads

2. **Caching**:
   - Implement Redis/Memcached for search results
   - Use Django's cache framework
   - Cache static files with CDN

3. **API Optimization**:
   - Implement pagination
   - Use database query optimization
   - Add API rate limiting

### WordPress Optimization

1. **Frontend Optimization**:
   - Minify CSS/JS files
   - Use browser caching
   - Optimize images

2. **Performance Monitoring**:
   - Monitor API response times
   - Track search usage patterns
   - Optimize based on user behavior

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review Django and WordPress logs
3. Create an issue in the GitHub repository
4. Contact the URI Libraries development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Changelog

### Version 1.0.0
- Initial release
- Django backend with XML indexing
- WordPress plugin with search interface
- Support for 283+ XML files from URI web archives
- Responsive design with pagination
- Production deployment instructions
