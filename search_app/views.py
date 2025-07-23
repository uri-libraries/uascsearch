from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import XMLDocument
from django.core.paginator import Paginator
import re

@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = min(int(request.GET.get('per_page', 10)), 50)  # Max 50 results per page

    if not query:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Please provide a search query'
        })

    # Search in relevant fields only
    results = XMLDocument.objects.filter(
        Q(title__icontains=query) |
        Q(creator__icontains=query) |
        Q(dates__icontains=query) |
        Q(abstract__icontains=query)
    ).order_by('-updated_at')

    # Paginate results
    paginator = Paginator(results, per_page)
    page_obj = paginator.get_page(page)

    def highlight_text(text, query):
        """Add HTML highlighting to search terms"""
        if not query or not text:
            return text

        # Escape HTML in the text first
        text = str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Create a pattern that matches the query (case insensitive)
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        # Replace with highlighted version
        highlighted = pattern.sub(f'<mark>{query}</mark>', text)

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

