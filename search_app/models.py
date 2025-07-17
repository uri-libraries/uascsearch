from django.db import models

class XMLDocument(models.Model):
    filename = models.CharField(max_length=255)
    content = models.TextField()

