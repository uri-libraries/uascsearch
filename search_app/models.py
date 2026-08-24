from django.db import models
from django.utils import timezone
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET


def normalize_dublin_core(dublin_core):
    """Clean repeatable Dublin Core values for API and display consumers."""
    placeholder_patterns = (
        r'^(?:abstract text|scope(?: and content)? note(?: for series)?|'
        r'arrangement(?: note(?: for series)?)?|series dates)$',
        r'^#?\s*boxes(?:\s*\([^)]*\))?$',
        r'^corp name$',
    )
    normalized = {}

    for field, values in (dublin_core or {}).items():
        if isinstance(values, str):
            values = [values]
        cleaned_values = []
        for value in values or []:
            value = re.sub(r'\s+', ' ', unquote(str(value))).strip()
            value = re.sub(r'^(?:corp(?:orate)?|personal) name\s*:?\s*', '', value, flags=re.IGNORECASE)
            if field != 'source':
                value = re.sub(r'\s*(?:\\+|/\s*)$', '', value).strip()
            if not value or any(re.fullmatch(pattern, value, re.IGNORECASE) for pattern in placeholder_patterns):
                continue
            if re.search(r'\bX{2,}\b', value, re.IGNORECASE):
                continue
            if value.casefold() not in {item.casefold() for item in cleaned_values}:
                cleaned_values.append(value[:32000])
        normalized[field] = cleaned_values

    return normalized


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
    metadata = models.JSONField(default=dict, blank=True)
    dublin_core = models.JSONField(default=dict, blank=True)
    subjects = models.TextField(blank=True)  # Store extracted subject terms
    url = models.URLField(blank=True, null=True)
    eadid = models.CharField(max_length=255, blank=True)
    public_url = models.URLField(blank=True)
    is_deleted = models.BooleanField(default=False)
    file_size = models.IntegerField(default=0)
    last_modified = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    indexed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def get_oai_identifier(self):
        base = self.eadid if self.eadid else self.filename.rsplit('.', 1)[0]
        return f'oai:uascsearch.library.uri.edu:{base}'

    def get_dublin_core(self):
        """Return normalized Dublin Core fields, including legacy-record fallback."""
        if self.dublin_core:
            return normalize_dublin_core(self.dublin_core)

        return normalize_dublin_core({
            'title': [self.title] if self.title else [],
            'creator': [self.creator] if self.creator else [],
            'description': [self.abstract] if self.abstract else [],
            'subject': [value.strip() for value in self.subjects.split(';') if value.strip()],
            'date': [self.dates] if self.dates else [],
            'type': ['Archival finding aid'],
            'identifier': [self.eadid] if self.eadid else [],
            'source': [self.public_url or self.url] if (self.public_url or self.url) else [],
            'publisher': ['University of Rhode Island Libraries'],
            'rights': ['Contact the repository regarding access and reuse.'],
        })

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

