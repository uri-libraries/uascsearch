# Manual Setup Guide

This guide provides step-by-step manual installation instructions for the URI XML Search system.

## Prerequisites

- **Python 3.8+**
- **Apache with mod_wsgi** OR **Nginx with uWSGI**
- **Git**
- **Virtual environment** (recommended)
- **Root/sudo access** to the server

## Step 1: System Preparation

### Amazon Linux / AlmaLinux
```bash
sudo dnf update -y  # or 'yum' for AL2
sudo dnf install -y python3 python3-pip python3-devel httpd httpd-devel gcc git
sudo pip3 install mod_wsgi
```

## Step 2: Application Setup

### Clone Repository
```bash
sudo mkdir -p /var/www/uascsearch
cd /var/www/uascsearch
sudo git clone https://github.com/uri-libraries/uascsearch.git .
```

### Create Virtual Environment
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install -r requirements.txt
```

### Set Ownership
```bash
sudo chown -R apache:apache /var/www/uascsearch
```

## Step 3: Environment Configuration

### Create Environment File
```bash
sudo cp /var/www/uascsearch/.env.template /var/www/uascsearch/.env
sudo nano /var/www/uascsearch/.env
```

### Configure Environment Variables
```bash
# Generate a strong secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Edit .env file
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
CORS_ALLOWED_ORIGINS=https://your-wordpress-site.com
```

## Step 4: Database Setup

```bash
cd /var/www/uascsearch

# Run migrations
sudo -u apache venv/bin/python manage.py migrate

# Create superuser (optional)
sudo -u apache venv/bin/python manage.py createsuperuser

# Collect static files
sudo -u apache venv/bin/python manage.py collectstatic --noinput
```

## Step 5: Apache Configuration

Create configuration:
```bash
sudo nano /etc/httpd/conf.d/uascsearch.conf
```

Add configuration:
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    DocumentRoot /var/www/uascsearch
    
    WSGIDaemonProcess uascsearch python-path=/var/www/uascsearch python-home=/var/www/uascsearch/venv user=apache group=apache
    WSGIProcessGroup uascsearch
    WSGIScriptAlias / /var/www/uascsearch/config/wsgi.py
    
    <Directory /var/www/uascsearch/config>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    
    Alias /static/ /var/www/uascsearch/static/
    <Directory /var/www/uascsearch/static>
        Require all granted
    </Directory>
    
    Alias /media/ /var/www/uascsearch/media/
    <Directory /var/www/uascsearch/media>
        Require all granted
    </Directory>
    
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options SAMEORIGIN
    Header always set X-XSS-Protection "1; mode=block"
    
    ErrorLog ${APACHE_LOG_DIR}/uascsearch_error.log
    CustomLog ${APACHE_LOG_DIR}/uascsearch_access.log combined
</VirtualHost>
```

Enable and start Apache:
```bash
sudo systemctl start httpd
sudo systemctl enable httpd
sudo httpd -t  # Test configuration
```

## Step 6: SELinux Configuration

If SELinux is enabled:
```bash
# Check SELinux status
getenforce

# Set required booleans
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_connect_db 1

# Set file contexts
sudo semanage fcontext -a -t httpd_config_t "/var/www/uascsearch(/.*)?"
sudo semanage fcontext -a -t httpd_exec_t "/var/www/uascsearch/venv/bin/python*"
sudo restorecon -Rv /var/www/uascsearch
```

## Step 7: Firewall Configuration

### Firewalld
```bash
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Manual iptables
```bash
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

## Step 8: SSL Certificate Setup

### Let's Encrypt (Recommended)

Install Certbot:
```bash
sudo dnf install -y certbot python3-certbot-apache
```

Obtain certificate:
```bash
sudo certbot --apache -d your-domain.com -d www.your-domain.com
```

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

### Self-Signed Certificate (Development/Testing)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/uascsearch.key \
    -out /etc/ssl/certs/uascsearch.crt \
    -subj "/C=US/ST=RI/L=Kingston/O=URI/CN=your-domain.com"

sudo chmod 600 /etc/ssl/private/uascsearch.key
```

Add SSL VirtualHost to Apache configuration:
```apache
<VirtualHost *:443>
    ServerName your-domain.com
    DocumentRoot /var/www/uascsearch
    
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/uascsearch.crt
    SSLCertificateKeyFile /etc/ssl/private/uascsearch.key
    
    # Same WSGI and directory configuration as HTTP version
    # ... (copy from above)
    
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
</VirtualHost>
```

## Step 9: Index XML Files

```bash
cd /var/www/uascsearch

# Test with a few files first
sudo -u apache venv/bin/python manage.py index_xml --max-files 5 --delay 2.0 --clear

# Index all files (this may take 30+ minutes)
sudo -u apache venv/bin/python manage.py index_xml --clear --delay 1.0
```

## Step 10: Testing

### Test API Endpoint
```bash
curl "http://your-domain.com/search/?q=test"
curl "https://your-domain.com/search/?q=history"
```

### Test Admin Interface
Visit: `https://your-domain.com/admin/`

### Test Standalone Search Page
Visit: `https://your-domain.com/standalone-search/`

## WordPress Integration

### Option 1: JavaScript Plugin

1. Upload `wordpress-integration/uri-xml-search.php` to `/wp-content/plugins/uri-xml-search/`
2. Upload supporting files (`uri-xml-search.js`, `uri-xml-search.css`)
3. Activate plugin in WordPress admin
4. Configure API URL in plugin settings
5. Add shortcode: `[uri_xml_search]`

### Option 2: PHP-Only Plugin

1. Upload `wordpress-integration/uri-xml-search-nojs.php` to `/wp-content/plugins/uri-xml-search-nojs/`
2. Upload `uri-xml-search-nojs.css`
3. Activate and configure as above

### Option 3: Iframe Integration

1. Add iframe to WordPress page:
```html
<iframe src="https://your-domain.com/standalone-search/" width="100%" height="600" style="border:1px solid #ccc;"></iframe>
```

## Troubleshooting

### Check Apache Status
```bash
sudo systemctl status httpd
```

### View Error Logs
```bash
sudo tail -f /var/log/httpd/uascsearch_error.log
```

### Test Django Directly
```bash
cd /var/www/uascsearch
sudo -u apache venv/bin/python manage.py check
```

### Check File Permissions
```bash
ls -la /var/www/uascsearch/
# Should show apache:apache ownership
```

### Test WSGI Module
```bash
httpd -M | grep wsgi
```

## Performance Tuning

### Apache MPM Configuration

Edit `/etc/httpd/conf.modules.d/00-mpm.conf`:

```apache
<IfModule mpm_prefork_module>
    StartServers             8
    MinSpareServers          5
    MaxSpareServers         20
    ServerLimit            256
    MaxRequestWorkers      256
    MaxConnectionsPerChild   0
</IfModule>
```

### WSGI Process Tuning

For high traffic, adjust WSGI processes:
```apache
WSGIDaemonProcess uascsearch processes=4 threads=15 python-path=/var/www/uascsearch python-home=/var/www/uascsearch/venv
```

### Database Optimization

Consider PostgreSQL for production:
```bash
# Install PostgreSQL
sudo dnf install postgresql postgresql-server python3-psycopg2

# Create database and user
sudo -u postgres createdb uascsearch
sudo -u postgres createuser --interactive uascsearch_user

# Update Django settings.py to use PostgreSQL
```

## Maintenance

### Regular Updates
```bash
# Update system packages
sudo dnf update

# Update Python packages
cd /var/www/uascsearch
sudo venv/bin/pip install --upgrade -r requirements.txt

# Restart Apache
sudo systemctl restart httpd
```

### Re-index XML Files
```bash
# Weekly or monthly re-indexing
sudo -u apache venv/bin/python manage.py index_xml --clear --delay 1.0
```

### Backup Database
```bash
cd /var/www/uascsearch
sudo -u apache venv/bin/python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

This manual setup provides complete control over the installation process and allows for customization based on your specific server environment and requirements.
