# URI XML Search System

A Django REST API backend with WordPress frontend integration for searching URI Special Collections XML archives.

## Overview

This system indexes and searches hundreds of XML files from the URI web archives (`https://webarchives.apps.uri.edu/xml/`) through a user-friendly WordPress interface.

**Architecture:**
- **Backend**: Django REST API with XML indexing
- **Frontend**: WordPress plugin with search interface  
- **Data Source**: URI web archives XML collection

## Quick Start

### Automated Installation (Recommended)

**Production (Amazon Linux/EC2):**
```bash
git clone https://github.com/uri-libraries/uascsearch.git
cd uascsearch
sudo ./deploy-amazon-linux.sh
```

**Development (AlmaLinux/RHEL-based):**
```bash
git clone https://github.com/uri-libraries/uascsearch.git
cd uascsearch
sudo ./deploy-dev.sh
```

The automated scripts handle:
- Package installation (Apache, Python, mod_wsgi)
- Virtual environment setup
- Database migrations
- Static file collection
- SSL-ready configuration (production)
- Development server setup (development)
- XML indexing

### Manual Installation

See [MANUAL_SETUP.md](MANUAL_SETUP.md) for detailed manual installation steps.

## WordPress Integration

Three integration options available in the `wordpress-integration/` directory:

1. **JavaScript Plugin** (`uri-xml-search.php`) - Full-featured for unrestricted sites
2. **PHP-only Plugin** (`uri-xml-search-nojs.php`) - For sites that block JavaScript  
3. **Iframe Integration** (`standalone-search.html`) - Embed search page in iframe

**Quick Setup:**
1. Choose appropriate plugin from `wordpress-integration/`
2. Upload to `/wp-content/plugins/` and activate
3. Add shortcode: `[uri_xml_search]`
4. Configure API URL in plugin settings

## Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ip
CORS_ALLOWED_ORIGINS=https://your-wordpress-site.com
```

### SSL Setup (Let's Encrypt)

```bash
# Install certbot
sudo dnf install certbot python3-certbot-apache

# Get certificate
sudo certbot --apache -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

## Usage

### Management Commands

```bash
# Index XML files
python manage.py index_xml --clear --delay 1.0

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### API Endpoints

- `GET /search/?q=query` - Search XML documents
- `GET /standalone-search/` - Standalone search page (for iframe)
- `GET /admin/` - Django admin interface

## File Structure

```
uascsearch/
├── .env.template                 # Environment variables template
├── .gitignore                   # Git ignore patterns
├── deploy-amazon-linux.sh       # Production deployment script
├── deploy-dev.sh                # Development deployment script
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── MANUAL_SETUP.md             # Detailed manual installation guide
├── search_app/                 # Django app
│   ├── models.py               # XMLDocument model
│   ├── views.py                # API views
│   ├── management/commands/    # index_xml command
│   └── templates/              # HTML templates
├── config/                     # Django project settings
│   ├── settings.py             # Django configuration
│   ├── urls.py                 # URL routing
│   └── wsgi.py                 # WSGI application
├── wordpress-integration/      # WordPress plugins
└── sample_xml/                 # Sample XML files
```

## Troubleshooting

### Common Issues

**Search returns no results:**
```bash
# Check if files are indexed
python manage.py shell -c "from search_app.models import XMLDocument; print(XMLDocument.objects.count())"

# Re-index if needed
python manage.py index_xml --clear
```

**Apache/WSGI errors:**
```bash
# Check Apache syntax
sudo httpd -t

# View error logs
sudo tail -f /var/log/httpd/error.log
```

**Permission errors:**
```bash
# Fix ownership
sudo chown -R apache:apache /var/www/uascsearch

# SELinux
sudo setsebool -P httpd_can_network_connect 1
sudo restorecon -Rv /var/www/uascsearch
```

**WordPress iframe blank:**
- Ensure both sites use same protocol (HTTP/HTTPS)
- Check X-Frame-Options setting in Django
- Verify CORS configuration

### Logs

- **Django**: Check Apache error logs
- **WordPress**: Enable WP_DEBUG in wp-config.php
- **API**: Test directly with curl: `curl "http://your-site.com/search/?q=test"`

## Development

### Local Development

**Quick Setup (AlmaLinux/RHEL):**
```bash
sudo ./deploy-dev.sh
cd ~/uascsearch-dev
./start-dev.sh
```

**Manual Setup:**
```bash
# Clone and setup
git clone https://github.com/uri-libraries/uascsearch.git
cd uascsearch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Index some test files
python manage.py index_xml --max-files 5

# Run development server
python manage.py runserver 0.0.0.0:8000

# For HTTPS testing
pip install django-extensions Werkzeug pyOpenSSL
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
```

### Adding Features

1. **New search fields**: Modify `search_app/models.py` and `views.py`
2. **WordPress customization**: Edit files in `wordpress-integration/`
3. **Styling changes**: Update templates in `search_app/templates/`

## Production Deployment

### Security Checklist

- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` (use environment variable)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Firewall configured (ports 80, 443)
- [ ] Regular backups of database
- [ ] Keep Django and dependencies updated

### Performance Optimization

- Use database indexing for search fields
- Implement caching (Redis/Memcached)
- Configure Apache for compression and caching
- Consider CDN for static files
- Monitor with tools like New Relic or Datadog

## Support

- **Issues**: [GitHub Issues](https://github.com/uri-libraries/uascsearch/issues)
- **Documentation**: Check included markdown files
- **Logs**: Always include relevant log output when reporting issues

## License

MIT License - see LICENSE file for details.
