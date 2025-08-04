#!/bin/bash

# URI XML Search Development Deployment Script
# For local development on AlmaLinux/RHEL-based systems
# Run this script as root or with sudo privileges

set -e

echo "Setting up URI XML Search System for Development..."
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run this script as root or with sudo"
    exit 1
fi

# Detect package manager
if command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
    echo "Detected RHEL-based system (using dnf)"
elif command -v yum &> /dev/null; then
    PACKAGE_MANAGER="yum"
    echo "Detected RHEL-based system (using yum)"
else
    echo "ERROR: Cannot detect package manager. This script is for RHEL-based systems."
    exit 1
fi

# Update system
echo "Updating system packages..."
$PACKAGE_MANAGER update -y

# Install EPEL repository
echo "Installing EPEL repository..."
$PACKAGE_MANAGER install -y epel-release

# Install required packages for development
echo "Installing required packages..."
$PACKAGE_MANAGER install -y python3 python3-pip python3-devel git gcc sqlite-devel

# Install httpd for production testing (optional)
read -p "Install Apache httpd for production testing? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    $PACKAGE_MANAGER install -y httpd httpd-devel python3-mod_wsgi
    systemctl enable httpd
    echo "Apache installed and enabled"
fi

# Get current user info
CURRENT_USER=${SUDO_USER:-$USER}
CURRENT_HOME=$(eval echo ~$CURRENT_USER)

# Set up development directory
DEV_DIR="$CURRENT_HOME/uascsearch-dev"
echo "Setting up development directory at $DEV_DIR..."

# Create development directory
mkdir -p "$DEV_DIR"
cd "$DEV_DIR"

# Clone or update repository
echo "Setting up application code..."
if [ -d ".git" ]; then
    echo "Updating existing repository..."
    sudo -u $CURRENT_USER git pull
else
    echo "Cloning repository..."
    sudo -u $CURRENT_USER git clone https://github.com/uri-libraries/uascsearch.git .
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
sudo -u $CURRENT_USER python3 -m venv venv
sudo -u $CURRENT_USER venv/bin/pip install --upgrade pip
sudo -u $CURRENT_USER venv/bin/pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
sudo -u $CURRENT_USER venv/bin/pip install django-extensions Werkzeug pyOpenSSL

# Create development environment file
echo "Creating development environment configuration..."
cat > "$DEV_DIR/.env" << EOF
# Development environment variables
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
# TODO: ADD YOUR DEVELOPMENT DOMAIN/IP IF NEEDED
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,$(hostname -I | awk '{print $1}')
# TODO: UPDATE THIS IF YOU HAVE A WORDPRESS SITE FOR TESTING
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
EOF

chown $CURRENT_USER:$CURRENT_USER "$DEV_DIR/.env"

# Run migrations
echo "Running database migrations..."
sudo -u $CURRENT_USER $DEV_DIR/venv/bin/python $DEV_DIR/manage.py migrate

# Create development superuser
echo ""
read -p "Create a development superuser? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating development superuser..."
    sudo -u $CURRENT_USER $DEV_DIR/venv/bin/python $DEV_DIR/manage.py createsuperuser
fi

# Index some test XML files
echo ""
read -p "Index some test XML files? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Indexing test XML files (max 10 files)..."
    sudo -u $CURRENT_USER $DEV_DIR/venv/bin/python $DEV_DIR/manage.py index_xml --max-files 10 --delay 2.0 --clear
fi

# Create development scripts
echo "Creating development helper scripts..."

# Create start script
cat > "$DEV_DIR/start-dev.sh" << 'EOF'
#!/bin/bash
# Start development server

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting Django development server..."
echo "Access the application at:"
echo "  - Main site: http://localhost:8000/"
echo "  - API: http://localhost:8000/search/"
echo "  - Admin: http://localhost:8000/admin/"
echo "  - Standalone search: http://localhost:8000/standalone-search/"
echo ""
echo "Press Ctrl+C to stop the server"

python manage.py runserver 0.0.0.0:8000
EOF

# Create HTTPS development script
cat > "$DEV_DIR/start-dev-https.sh" << 'EOF'
#!/bin/bash
# Start development server with HTTPS

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting Django development server with HTTPS..."
echo "Access the application at:"
echo "  - Main site: https://localhost:8000/"
echo "  - API: https://localhost:8000/search/"
echo "  - Admin: https://localhost:8000/admin/"
echo "  - Standalone search: https://localhost:8000/standalone-search/"
echo ""
echo "Note: You'll see SSL warnings in the browser (this is normal for development)"
echo "Press Ctrl+C to stop the server"

python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 0.0.0.0:8000
EOF

# Create index script
cat > "$DEV_DIR/index-xml.sh" << 'EOF'
#!/bin/bash
# Index XML files

cd "$(dirname "$0")"
source venv/bin/activate

echo "Indexing XML files..."
python manage.py index_xml --clear --delay 1.0
EOF

# Create shell script
cat > "$DEV_DIR/shell.sh" << 'EOF'
#!/bin/bash
# Django shell

cd "$(dirname "$0")"
source venv/bin/activate
python manage.py shell
EOF

# Make scripts executable
chmod +x "$DEV_DIR"/*.sh
chown $CURRENT_USER:$CURRENT_USER "$DEV_DIR"/*.sh

# Set proper ownership
chown -R $CURRENT_USER:$CURRENT_USER "$DEV_DIR"

# Configure firewall for development (if firewalld is running)
if systemctl is-active --quiet firewalld; then
    echo "Configuring firewall for development..."
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --reload
    echo "SUCCESS: Port 8000 opened for development server"
fi

echo ""
echo "SUCCESS: Development environment setup complete!"
echo ""
echo "Development directory: $DEV_DIR"
echo ""
echo "IMPORTANT: To customize for your setup, edit these files:"
echo "  - $DEV_DIR/.env (update ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS)"
echo ""
echo "Quick start commands:"
echo "  cd $DEV_DIR"
echo "  ./start-dev.sh          # Start HTTP development server"
echo "  ./start-dev-https.sh    # Start HTTPS development server"
echo "  ./index-xml.sh          # Index XML files"
echo "  ./shell.sh              # Django shell"
echo ""
echo "Manual commands:"
echo "  source venv/bin/activate                    # Activate virtual environment"
echo "  python manage.py runserver 0.0.0.0:8000   # Start development server"
echo "  python manage.py index_xml --max-files 5   # Index a few test files"
echo "  python manage.py createsuperuser           # Create admin user"
echo ""
echo "Access URLs (after starting dev server):"
echo "  - Main application: http://localhost:8000/"
echo "  - Search API: http://localhost:8000/search/"
echo "  - Admin interface: http://localhost:8000/admin/"
echo "  - Standalone search: http://localhost:8000/standalone-search/"
echo ""
echo "NOTE: For production deployment, you'll need to configure:"
echo "  - Domain names in Apache configuration"
echo "  - ALLOWED_HOSTS for your production domains"
echo "  - CORS_ALLOWED_ORIGINS for WordPress integration"
echo ""
