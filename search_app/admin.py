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
    def save_model(self, request, obj, form, change):
        if 'title' in form.changed_data:
            obj.title_manually_edited = True
        super().save_model(request, obj, form, change)
    list_display = ['clean_filename', 'clean_title', 'clean_creator', 'indexed_at', 'file_size']
    list_filter = ['indexed_at', 'content_type']
    search_fields = ['filename', 'title', 'creator', 'abstract']
    readonly_fields = ['indexed_at', 'updated_at', 'file_size', 'last_modified', 
                      'clean_filename_display', 'clean_title_display', 'clean_creator_display', 'clean_abstract_display']
    
    def clean_filename(self, obj):
        """Display filename with URL decoding and cleaned up"""
        import urllib.parse
        cleaned = urllib.parse.unquote(obj.filename)
        cleaned = cleaned.replace('.xml', '').replace('_', ' ').replace('%', ' ')
        return cleaned[:50] + '...' if len(cleaned) > 50 else cleaned
    clean_filename.short_description = 'Filename'
    clean_filename.admin_order_field = 'filename'
    
    def clean_title(self, obj):
        """Display title with URL decoding and cleaned up"""
        import urllib.parse
        import re
        
        title = obj.title or obj.filename.replace('.xml', '')
        # URL decode
        cleaned = urllib.parse.unquote(title)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Remove common artifacts
        cleaned = re.sub(r'^\d+-\d+-\d+ onLoad.*?Website:\s*', '', cleaned)
        cleaned = re.sub(r'^mailto:.*?Website:\s*', '', cleaned)
        # Limit length for display
        return cleaned[:80] + '...' if len(cleaned) > 80 else cleaned
    clean_title.short_description = 'Title'
    clean_title.admin_order_field = 'title'
    
    def clean_creator(self, obj):
        """Display creator with cleaned up text"""
        import urllib.parse
        import re
        
        creator = obj.creator
        if not creator:
            return ''
        
        # URL decode
        cleaned = urllib.parse.unquote(creator)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Remove MARC codes and other artifacts
        cleaned = re.sub(r'\s+\d+\$[a-z]\s+', ' ', cleaned)
        cleaned = re.sub(r'primary \d+\$[a-z].*', '', cleaned)
        # Limit length for display
        return cleaned[:60] + '...' if len(cleaned) > 60 else cleaned
    clean_creator.short_description = 'Creator'
    clean_creator.admin_order_field = 'creator'
    
    fieldsets = (
        ('File Information', {
            'fields': ('clean_filename_display', 'url', 'file_size', 'content_type', 'last_modified')
        }),
        ('Content Fields', {
            'fields': ('clean_title_display', 'clean_creator_display', 'dates', 'clean_abstract_display')
        }),
        ('Raw Fields', {
            'fields': ('filename', 'title', 'creator', 'abstract'),
            'classes': ('collapse',),
            'description': 'Raw stored data (URL-encoded)'
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
    
    def clean_filename_display(self, obj):
        """Clean filename for detail view"""
        return self.clean_filename(obj)
    clean_filename_display.short_description = 'Clean Filename'
    
    def clean_title_display(self, obj):
        """Clean title for detail view"""
        return self.clean_title(obj)
    clean_title_display.short_description = 'Clean Title'
    
    def clean_creator_display(self, obj):
        """Clean creator for detail view"""
        return self.clean_creator(obj)
    clean_creator_display.short_description = 'Clean Creator'
    
    def clean_abstract_display(self, obj):
        """Clean abstract for detail view"""
        import urllib.parse
        import re
        
        abstract = obj.abstract
        if not abstract:
            return ''
        
        # URL decode
        cleaned = urllib.parse.unquote(abstract)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        # Remove MARC codes and other artifacts
        cleaned = re.sub(r'\s+\d+\$[a-z]\s+', ' ', cleaned)
        cleaned = re.sub(r'primary \d+\$[a-z].*', '', cleaned)
        return cleaned
    clean_abstract_display.short_description = 'Clean Abstract'
    
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
