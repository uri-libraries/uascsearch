from django.urls import path
from .views import search, standalone_search

urlpatterns = [
    path('search/', search, name='search'),
    path('standalone-search/', standalone_search, name='standalone_search'),
]

