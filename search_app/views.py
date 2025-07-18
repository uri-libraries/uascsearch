from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import XMLDocument
from django.core.paginator import Paginator

@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))
    
    if not query:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Please provide a search query'
        })
    
    # Search in both filename and content
    results = XMLDocument.objects.filter(
        Q(content__icontains=query) | Q(filename__icontains=query)
    ).order_by('-updated_at')
    
    # Paginate results
    paginator = Paginator(results, per_page)
    page_obj = paginator.get_page(page)
    
    response_data = {
        'results': [
            {
                'filename': doc.filename,
                'url': doc.url,
                'snippet': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                'file_size': doc.file_size,
                'last_modified': doc.last_modified,
                'indexed_at': doc.indexed_at.isoformat() if doc.indexed_at else None,
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

