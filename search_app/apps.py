from django.apps import AppConfig


class SearchAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search_app'
    verbose_name = 'University Archives and Special Collections'
    
    def ready(self):
        # Configure admin site
        from django.contrib import admin
        admin.site.site_header = "UASC Search System Administration"
        admin.site.site_title = "UASC Admin"
        admin.site.index_title = "University Archives and Special Collections"
