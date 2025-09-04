from django.http import HttpResponseRedirect

class RootRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only redirect the root URL, not /admin, /search, etc.
        if request.path == '/':
            return HttpResponseRedirect('https://web.uri.edu/specialcollections/')
        return self.get_response(request)
