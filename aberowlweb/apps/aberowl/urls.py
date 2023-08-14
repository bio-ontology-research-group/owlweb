from django.urls import include, path
from .views import MainView, OntologyListView, OntologyDetailView

urlpatterns = [
    path('', MainView.as_view(), name='aberowl-main'),
    path('ontology/', OntologyListView.as_view(), name='ontology-list'),
    path('ontology/<str:onto>/', OntologyDetailView.as_view(), name='ontology'),
    path('api/', include('aberowl.api_urls')),
    path('manage/', include('aberowl.manage_urls')),
]
