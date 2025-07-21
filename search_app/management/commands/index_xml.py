from django.core.management.base import BaseCommand
from search_app.models import XMLDocument
import xml.etree.ElementTree as ET
import requests
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import re

class Command(BaseCommand):
    help = 'Index XML files from URI web archives'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', type=str, 
                          default='https://webarchives.apps.uri.edu/xml/',
                          help='Base URL of the directory containing XML files')
        parser.add_argument('--clear', action='store_true', 
                          help='Clear existing documents before indexing')
        parser.add_argument('--delay', type=float, default=1.0,
                          help='Delay between requests in seconds (default: 1.0)')
        parser.add_argument('--max-files', type=int, default=None,
                          help='Maximum number of files to process (for testing)')

    def handle(self, *args, **options):
        base_url = options['base_url']
        delay = options['delay']
        max_files = options['max_files']
        
        if options['clear']:
            self.stdout.write('Clearing existing documents...')
            XMLDocument.objects.all().delete()
            
        self.stdout.write(f'Starting to index XML files from: {base_url}')
        
        try:
            # Get list of XML files from the directory
            xml_files = self.discover_xml_files(base_url)
            self.stdout.write(f'Found {len(xml_files)} XML files to index')
            
            if max_files:
                xml_files = xml_files[:max_files]
                self.stdout.write(f'Limiting to first {max_files} files for testing')
            
            indexed_count = 0
            error_count = 0
            
            for xml_file in xml_files:
                try:
                    self.stdout.write(f'Processing: {xml_file}')
                    
                    # Download and parse XML file
                    response = requests.get(xml_file, timeout=30)
                    response.raise_for_status()
                    
                    # Check if it's actually XML content
                    if not response.content.strip().startswith(b'<?xml'):
                        self.stdout.write(f'⚠ Skipping {xml_file}: Not valid XML')
                        continue
                    
                    # Parse XML content
                    try:
                        root = ET.fromstring(response.content)
                    except ET.ParseError as e:
                        self.stdout.write(f'⚠ XML Parse Error for {xml_file}: {str(e)}')
                        continue
                    
                    content = self.extract_text_content(root)
                    
                    # Skip if content is too short (likely empty or invalid)
                    if len(content.strip()) < 50:
                        self.stdout.write(f'⚠ Skipping {xml_file}: Content too short')
                        continue
                    
                    # Extract filename
                    filename = os.path.basename(urlparse(xml_file).path)
                    
                    # Save to database
                    document, created = XMLDocument.objects.update_or_create(
                        filename=filename,
                        defaults={
                            'content': content,
                            'url': xml_file,
                            'file_size': len(response.content),
                            'last_modified': response.headers.get('Last-Modified', ''),
                            'content_type': response.headers.get('Content-Type', ''),
                            'title': '',  # Will be set below
                        }
                    )
                    
                    # Extract and save title
                    document.title = document.extract_title_from_content()
                    document.save()
                    
                    indexed_count += 1
                    self.stdout.write(f'✓ Indexed: {filename} ({len(content)} chars)')
                    
                    # Add delay to be respectful to the server
                    time.sleep(delay)
                    
                except requests.exceptions.RequestException as e:
                    error_count += 1
                    self.stdout.write(f'✗ Network error for {xml_file}: {str(e)}')
                except Exception as e:
                    error_count += 1
                    self.stdout.write(f'✗ Error processing {xml_file}: {str(e)}')
                    
            self.stdout.write(f'\nIndexing complete!')
            self.stdout.write(f'Successfully indexed: {indexed_count} files')
            self.stdout.write(f'Errors: {error_count} files')
            
        except Exception as e:
            self.stdout.write(f'Error: {str(e)}')

    def discover_xml_files(self, base_url):
        """Discover XML files in the URI web archives directory"""
        xml_files = []
        
        try:
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML directory listing
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that end with .xml
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.xml') and not href.startswith('..'):
                    full_url = urljoin(base_url, href)
                    xml_files.append(full_url)
                    
            # Also look for links that might be XML files without .xml extension
            # but contain XML-like patterns
            for link in soup.find_all('a', href=True):
                href = link['href']
                if re.search(r'\.(xml|rdf|atom|rss)$', href, re.IGNORECASE):
                    full_url = urljoin(base_url, href)
                    if full_url not in xml_files:
                        xml_files.append(full_url)
                        
        except Exception as e:
            self.stdout.write(f'Error discovering XML files: {str(e)}')
            
        return xml_files

    def extract_text_content(self, element):
        """Extract all text content from XML element"""
        text_content = []
        
        # Add element text
        if element.text:
            text_content.append(element.text.strip())
            
        # Add attribute values (but filter out URLs and IDs to reduce noise)
        for attr_name, attr_value in element.attrib.items():
            if not attr_name.lower() in ['id', 'href', 'src', 'url', 'xmlns']:
                text_content.append(str(attr_value))
            
        # Recursively process child elements
        for child in element:
            text_content.append(self.extract_text_content(child))
            
        # Add tail text
        if element.tail:
            text_content.append(element.tail.strip())
            
        return ' '.join(filter(None, text_content))

