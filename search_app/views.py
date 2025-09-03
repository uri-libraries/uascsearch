from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import XMLDocument
from django.core.paginator import Paginator
from django.shortcuts import render
import re

@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = min(int(request.GET.get('per_page', 10)), 50)

    if not query:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Please provide a search query'
        })

    results = XMLDocument.objects.filter(
        Q(title__icontains=query) |
        Q(creator__icontains=query) |
        Q(dates__icontains=query) |
        Q(abstract__icontains=query)
    ).order_by('-updated_at')

    paginator = Paginator(results, per_page)
    page_obj = paginator.get_page(page)

    def highlight_text(text, query):
        if not query or not text:
            return text
        text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        # Use a lambda function to preserve the original text's capitalization
        highlighted = pattern.sub(lambda match: f'<mark>{match.group(0)}</mark>', text)
        return highlighted

    response_data = {
        'results': [
            {
                'filename': doc.filename,
                'title': highlight_text(doc.extract_title_from_content(), query),
                'url': doc.url,
                'snippet': highlight_text(doc.get_clean_snippet(query, 300), query),
                'file_size': doc.file_size,
                'last_modified': doc.last_modified,
                'indexed_at': doc.indexed_at.isoformat(),
            }
            for doc in page_obj
        ],
        'count': paginator.count,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'query': query,
    }

    return Response(response_data)

def standalone_search(request):
    """Render standalone search page for iframe embedding"""
    return render(request, "search_app/standalone-search.html")

def search_page(request):
    """Render main search page with full site layout"""
    return render(request, "search_app/search-page.html")
