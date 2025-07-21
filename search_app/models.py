from django.db import models
from django.utils import timezone
import re
import xml.etree.ElementTree as ET

class XMLDocument(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    title = models.CharField(max_length=500, blank=True)  # Add human-readable title
    url = models.URLField(blank=True, null=True)
    file_size = models.IntegerField(default=0)
    last_modified = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    indexed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or self.filename

    def get_clean_snippet(self, query='', max_length=200):
        """Extract a clean snippet from specific XML fields, highlighting search terms"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.content, 'html.parser')

            # Combine content from specific fields
            fields = ['Creator', 'Title', 'Dates', 'Abstract']
            field_content = []
            for field in fields:
                element = soup.find('td', string=re.compile(fr'{field}:', re.IGNORECASE))
                if element:
                    next_td = element.find_next('td')
                    if next_td and next_td.get_text(strip=True):
                        field_content.append(next_td.get_text(strip=True))

            combined_content = ' '.join(field_content)

            # Highlight query in the combined content
            if query:
                query_lower = query.lower()
                content_lower = combined_content.lower()
                pos = content_lower.find(query_lower)
                if pos != -1:
                    start = max(0, pos - 100)
                    end = min(len(combined_content), pos + len(query) + 100)
                    snippet = combined_content[start:end]
                    if start > 0:
                        snippet = '...' + snippet
                    if end < len(combined_content):
                        snippet = snippet + '...'
                    return snippet

            # Return the beginning of the combined content if no query
            snippet = combined_content[:max_length]
            if len(combined_content) > max_length:
                snippet += '...'
            return snippet

        except Exception as e:
            print(f"Error generating snippet: {e}")

        return ''

    def extract_title_from_content(self):
        """Extract a human-readable title from specific XML fields"""
        try:
            from bs4 import BeautifulSoup
            import urllib.parse
            soup = BeautifulSoup(self.content, 'html.parser')

            # Look for the Title field specifically
            title_element = soup.find('td', string=re.compile(r'Title:', re.IGNORECASE))
            if title_element:
                next_td = title_element.find_next('td')
                if next_td and next_td.get_text(strip=True):
                    title = next_td.get_text(strip=True)[:200]  # Limit length
                    return urllib.parse.unquote(title)  # Decode URL-encoded characters

        except Exception as e:
            print(f"Error extracting title: {e}")

        # Fallback to filename without extension
        return urllib.parse.unquote(self.filename.replace('.xml', '').replace('_', ' ').replace('-', ' '))

    class Meta:
        ordering = ['-updated_at']

