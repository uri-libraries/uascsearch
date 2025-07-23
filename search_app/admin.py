from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.html import format_html
from django.core.management import call_command
from .models import XMLDocument
import threading
import time
import os

class XMLDocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'title', 'creator', 'indexed_at', 'file_size']
    list_filter = ['indexed_at', 'content_type']
    search_fields = ['filename', 'title', 'creator', 'abstract']
    readonly_fields = ['indexed_at', 'updated_at', 'file_size', 'last_modified']
    
    fieldsets = (
        ('File Information', {
            'fields': ('filename', 'url', 'file_size', 'content_type', 'last_modified')
        }),
        ('Content Fields', {
            'fields': ('title', 'creator', 'dates', 'abstract')
        }),
        ('Full Content', {
            'fields': ('content',),
            'classes': ('collapse',),  # Collapsed by default
            'description': 'Full XML content (if stored)'
        }),
        ('Timestamps', {
            'fields': ('indexed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reindex/', self.admin_site.admin_view(self.reindex_view), name='search_app_xmldocument_reindex'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['reindex_url'] = reverse('admin:search_app_xmldocument_reindex')
        return super().changelist_view(request, extra_context)
    
    def reindex_view(self, request):
        if request.method == 'POST':
            # Start reindexing in a background thread
            def run_reindex():
                try:
                    call_command('index_xml', '--clear', '--delay=1.0')
                except Exception as e:
                    # Log the error - in production you'd want proper logging
                    print(f"Reindex error: {e}")
            
            thread = threading.Thread(target=run_reindex)
            thread.daemon = True
            thread.start()
            
            messages.success(request, 'Reindexing started in the background. This may take several minutes to complete.')
            return HttpResponseRedirect(reverse('admin:search_app_xmldocument_changelist'))
        
        # For GET requests, show confirmation page
        from django.template.response import TemplateResponse
        context = {
            'title': 'Reindex XML Documents',
            'opts': self.model._meta,
            'has_permission': True,
        }
        return TemplateResponse(request, 'admin/reindex_confirmation.html', context)

# Register the model with the custom admin
admin.site.register(XMLDocument, XMLDocumentAdmin)
