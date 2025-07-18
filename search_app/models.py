from django.db import models
from django.utils import timezone

class XMLDocument(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    url = models.URLField(blank=True, null=True)
    file_size = models.IntegerField(default=0)
    last_modified = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    indexed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.filename

    class Meta:
        ordering = ['-updated_at']

