from rest_framework.decorators import api_view
from rest_framework.response import Response
from searchapp.models import XMLDocument

@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '')
    results = XMLDocument.objects.filter(content__icontains=query)
    return Response([{'filename': doc.filename, 'snippet': doc.content[:200]} for doc in results])

