#!/bin/bash

# URI XML Search Deployment Script for Amazon Linux
# Run this script as root or with sudo privileges

set -e

echo "Deploying URI XML Search System on Amazon Linux..."
echo "====================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run this script as root or with sudo"
    exit 1
fi

# Detect Amazon Linux version
if command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
    echo "Detected Amazon Linux 2022+ (using dnf)"
elif command -v yum &> /dev/null; then
    PACKAGE_MANAGER="yum"
    echo "Detected Amazon Linux 2 (using yum)"
else
    echo "ERROR: Cannot detect package manager. This script is for Amazon Linux only."
    exit 1
fi

# Handle Node.js package conflicts first
echo "Checking for Node.js package conflicts..."
if $PACKAGE_MANAGER list installed | grep -q nodejs; then
    echo "Removing conflicting Node.js packages..."
    $PACKAGE_MANAGER remove -y nodejs nodejs-npm nodejs-full-i18n 2>/dev/null || true
fi

# Update system
echo "Updating system packages..."
$PACKAGE_MANAGER update -y --skip-broken

# Install required packages
echo "Installing required packages..."
if [ "$PACKAGE_MANAGER" = "yum" ]; then
    # Amazon Linux 2
    $PACKAGE_MANAGER install -y httpd python3 python3-pip python3-devel httpd-devel python3-mod_wsgi git
    # Install additional development tools
    $PACKAGE_MANAGER groupinstall -y "Development Tools"
else
    # Amazon Linux 2022+
    $PACKAGE_MANAGER install -y httpd python3 python3-pip python3-devel httpd-devel python3-mod_wsgi git gcc
fi

# Install mod_wsgi if not available via package manager
if ! httpd -M 2>/dev/null | grep -q wsgi_module; then
    echo "Installing mod_wsgi from pip..."
    pip3 install mod_wsgi
    
    # Get mod_wsgi configuration
    MOD_WSGI_CONFIG=$(mod_wsgi-express module-config)
    echo "$MOD_WSGI_CONFIG" > /etc/httpd/conf.modules.d/10-wsgi.conf
fi

# Enable and start Apache
echo "Configuring Apache..."
systemctl enable httpd
systemctl start httpd

# Create directory
echo "Creating application directory..."
mkdir -p /var/www/uascsearch

# Get the directory where this script is located (should be the repo root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd /var/www/uascsearch

# Clone or update repository
echo "Setting up application code..."
if [ -d ".git" ]; then
    echo "Updating existing repository..."
    git pull
else
    echo "Copying repository from deployment source..."
    cp -r "$SCRIPT_DIR"/* .
    cp -r "$SCRIPT_DIR"/.[^.]* . 2>/dev/null || true
    # Initialize git if copying from a git repo
    if [ -d "$SCRIPT_DIR/.git" ]; then
        git init
        git add .
        git commit -m "Initial production deployment from local repository"
    fi
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Set proper ownership and SELinux contexts
echo "Setting file permissions and SELinux contexts..."
chown -R apache:apache /var/www/uascsearch
chmod -R 755 /var/www/uascsearch

# Set SELinux contexts if SELinux is enabled
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
    echo "Setting SELinux contexts..."
    setsebool -P httpd_can_network_connect 1
    setsebool -P httpd_can_network_connect_db 1
    semanage fcontext -a -t httpd_config_t "/var/www/uascsearch(/.*)?" 2>/dev/null || true
    semanage fcontext -a -t httpd_exec_t "/var/www/uascsearch/venv/bin/python*" 2>/dev/null || true
    restorecon -Rv /var/www/uascsearch
fi

# Create Apache configuration for Amazon Linux
echo "Configuring Apache for Amazon Linux..."
cat > /etc/httpd/conf.d/uascsearch.conf << 'EOF'
# URI XML Search Apache Configuration for Amazon Linux

<VirtualHost *:80>
    # TODO: UPDATE THESE DOMAIN NAMES FOR YOUR DEPLOYMENT
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    
    # Redirect HTTP to HTTPS (uncomment when SSL is configured)
    # RewriteEngine On
    # RewriteCond %{HTTPS} off
    # RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
    
    # For testing without SSL, serve directly
    DocumentRoot /var/www/uascsearch
    
    WSGIDaemonProcess uascsearch python-path=/var/www/uascsearch python-home=/var/www/uascsearch/venv user=apache group=apache
    WSGIProcessGroup uascsearch
    WSGIScriptAlias / /var/www/uascsearch/config/wsgi.py
    
    <Directory /var/www/uascsearch/config>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
    
    # Static files
    Alias /static/ /var/www/uascsearch/static/
    <Directory /var/www/uascsearch/static>
        Require all granted
    </Directory>
    
    # Media files
    Alias /media/ /var/www/uascsearch/media/
    <Directory /var/www/uascsearch/media>
        Require all granted
    </Directory>
    
    # Security headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options SAMEORIGIN
    Header always set X-XSS-Protection "1; mode=block"
    
    # Logging
    ErrorLog /var/log/httpd/uascsearch_error.log
    CustomLog /var/log/httpd/uascsearch_access.log combined
    LogLevel info
</VirtualHost>

# Uncomment and configure when you have SSL certificates
# <VirtualHost *:443>
#     # TODO: UPDATE THESE DOMAIN NAMES FOR YOUR DEPLOYMENT
#     ServerName your-domain.com
#     ServerAlias www.your-domain.com
#     
#     SSLEngine on
#     # TODO: UPDATE THESE SSL CERTIFICATE PATHS FOR YOUR DEPLOYMENT
#     SSLCertificateFile /path/to/your/certificate.crt
#     SSLCertificateKeyFile /path/to/your/private.key
#     SSLCertificateChainFile /path/to/your/certificate_chain.crt
#     
#     DocumentRoot /var/www/uascsearch
#     
#     WSGIDaemonProcess uascsearch-ssl python-path=/var/www/uascsearch python-home=/var/www/uascsearch/venv user=apache group=apache
#     WSGIProcessGroup uascsearch-ssl
#     WSGIScriptAlias / /var/www/uascsearch/config/wsgi.py
#     
#     <Directory /var/www/uascsearch/config>
#         <Files wsgi.py>
#             Require all granted
#         </Files>
#     </Directory>
#     
#     Alias /static/ /var/www/uascsearch/static/
#     <Directory /var/www/uascsearch/static>
#         Require all granted
#     </Directory>
#     
#     Alias /media/ /var/www/uascsearch/media/
#     <Directory /var/www/uascsearch/media>
#         Require all granted
#     </Directory>
#     
#     Header always set X-Content-Type-Options nosniff
#     Header always set X-Frame-Options SAMEORIGIN
#     Header always set X-XSS-Protection "1; mode=block"
#     Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
#     
#     ErrorLog /var/log/httpd/uascsearch_ssl_error.log
#     CustomLog /var/log/httpd/uascsearch_ssl_access.log combined
# </VirtualHost>
EOF

# Create environment file
echo "Creating environment configuration..."
cat > /var/www/uascsearch/.env << EOF
# Production environment variables for Amazon Linux
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
# TODO: UPDATE THESE DOMAIN NAMES AND IPS FOR YOUR DEPLOYMENT
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
# TODO: UPDATE THIS CORS ORIGIN FOR YOUR WORDPRESS SITE
CORS_ALLOWED_ORIGINS=https://your-wordpress-site.com
EOF

# Create directories for static and media files
echo "Creating static and media directories..."
mkdir -p /var/www/uascsearch/static
mkdir -p /var/www/uascsearch/media

# Collect static files
echo "Collecting static files..."
sudo -u apache /var/www/uascsearch/venv/bin/python /var/www/uascsearch/manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
sudo -u apache /var/www/uascsearch/venv/bin/python /var/www/uascsearch/manage.py migrate

# Set final permissions
chown -R apache:apache /var/www/uascsearch

# Create superuser (optional)
echo ""
read -p "Do you want to create a superuser account? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating superuser..."
    sudo -u apache /var/www/uascsearch/venv/bin/python /var/www/uascsearch/manage.py createsuperuser
fi

# Configure firewall
echo "Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    echo "SUCCESS: Firewall configured for HTTP and HTTPS"
else
    echo "WARNING: Firewall not configured. Make sure ports 80 and 443 are open."
fi

# Test Apache configuration
echo "Testing Apache configuration..."
httpd -t

# Ask about indexing XML files
echo ""
read -p "Do you want to index XML files now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting XML indexing (this may take a while)..."
    echo "INFO: You can monitor progress in another terminal with:"
    echo "   sudo -u apache /var/www/uascsearch/venv/bin/python /var/www/uascsearch/manage.py index_xml --clear"
    sudo -u apache /var/www/uascsearch/venv/bin/python /var/www/uascsearch/manage.py index_xml --clear --delay 1.0 &
    INDEXING_PID=$!
    echo "INFO: Indexing started in background (PID: $INDEXING_PID)"
fi

# Restart Apache
echo "Restarting Apache..."
systemctl restart httpd

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com/ || echo "unknown")

echo ""
echo "SUCCESS: Deployment complete!"
echo ""
echo "Server Details:"
echo "   - Public IP: $SERVER_IP"
echo "   - HTTP URL: http://$SERVER_IP/"
echo "   - Search API: http://$SERVER_IP/search/"
echo "   - Admin Panel: http://$SERVER_IP/admin/"
echo ""
echo "IMPORTANT: You need to configure the following for your deployment:"
echo "1. Update domain names in /etc/httpd/conf.d/uascsearch.conf"
echo "2. Update ALLOWED_HOSTS in /var/www/uascsearch/.env"
echo "3. Update CORS_ALLOWED_ORIGINS in /var/www/uascsearch/.env for WordPress integration"
echo ""
echo "Next steps:"
echo "1. Configure SSL certificates (recommended: Let's Encrypt)"
echo "2. Update DNS to point your domain to this server"
echo "3. Uncomment SSL configuration in /etc/httpd/conf.d/uascsearch.conf"
echo "4. Test WordPress integration"
echo ""
echo "Useful commands:"
echo "  - Check Apache status: systemctl status httpd"
echo "  - View error logs: tail -f /var/log/httpd/uascsearch_error.log"
echo "  - View access logs: tail -f /var/log/httpd/uascsearch_access.log"
echo "  - Restart Apache: systemctl restart httpd"
echo "  - Update application: cd /var/www/uascsearch && git pull && systemctl restart httpd"
echo ""
echo "SSL Setup with Let's Encrypt:"
echo "  1. Install certbot: $PACKAGE_MANAGER install -y certbot python3-certbot-apache"
echo "  2. Get certificate: certbot --apache -d your-domain.com"
echo "  3. Test renewal: certbot renew --dry-run"
echo ""

if [ ! -z "$INDEXING_PID" ] && kill -0 $INDEXING_PID 2>/dev/null; then
    echo "INFO: XML indexing is still running in background (PID: $INDEXING_PID)"
    echo "    You can check progress with: ps aux | grep index_xml"
fi
