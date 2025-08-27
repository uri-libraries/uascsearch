from django.db import models
from django.utils import timezone
import re
import xml.etree.ElementTree as ET

class XMLDocument(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    # Store only relevant content fields
    title = models.CharField(max_length=500, blank=True)
    title_manually_edited = models.BooleanField(default=False)
    creator = models.TextField(blank=True)
    dates = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    # Keep original content for reference (optional - can be removed to save more space)
    content = models.TextField(blank=True)  # Make this optional
    subjects = models.TextField(blank=True)  # Store extracted subject terms
    url = models.URLField(blank=True, null=True)
    file_size = models.IntegerField(default=0)
    last_modified = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    indexed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or self.filename

    def get_clean_snippet(self, query='', max_length=200):
        """Extract a clean snippet from the stored relevant fields"""
        # Combine content from only abstract, creator, and subjects for snippet
        field_content = []
        if self.abstract.strip():
            field_content.append(self.abstract.strip())
        if self.creator.strip():
            field_content.append(self.creator.strip())
        if self.subjects.strip():
            field_content.append(self.subjects.strip())

        combined_content = ' '.join(field_content)

        # Highlight query in the combined content
        if query and combined_content:
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

    def extract_title_from_content(self):
        """Extract a human-readable title from the stored title field or filename"""
        import urllib.parse
        
        # Use stored title if available
        if self.title and self.title.strip():
            return urllib.parse.unquote(self.title.strip()[:200])
        
        # Fallback to filename without extension
        return urllib.parse.unquote(self.filename.replace('.xml', '').replace('_', ' ').replace('-', ' '))

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "XML Document"
        verbose_name_plural = "XML Documents"

