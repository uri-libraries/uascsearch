from django.urls import path
from .views import search, standalone_search, search_page
from .views_oai import oai_endpoint

urlpatterns = [
    path('search/', search, name='search'),
    path('standalone-search/', standalone_search, name='standalone_search'),
    path('search-page/', search_page, name='search_page'),
    path('oai/', oai_endpoint, name='oai_endpoint'),
]

