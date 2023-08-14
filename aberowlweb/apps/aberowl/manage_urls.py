from django.urls import path
from django.contrib.auth.decorators import login_required
from . import manage_views as views

urlpatterns = [
    path('ontology/', login_required(views.MyOntologyListView.as_view()), name='list_ontology'),
    path('ontology/create/', login_required(views.OntologyCreateView.as_view()), name='create_ontology'),
    path('ontology/edit/<int:pk>/', login_required(views.OntologyUpdateView.as_view()), name='edit_ontology'),
    path('ontology/<int:onto_pk>/submission/create/', login_required(views.SubmissionCreateView.as_view()),
         name='create_submission'),
    path('ontology/<int:onto_pk>/submission/edit/<int:pk>/', login_required(views.SubmissionUpdateView.as_view()),
         name='edit_submission'),
]
