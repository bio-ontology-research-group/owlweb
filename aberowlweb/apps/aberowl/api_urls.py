from django.urls import path
from . import api_views

urlpatterns = [
    path('class/_startwith/',
         api_views.FindClassByMethodStartWithAPIView.as_view(), name='api-find_class_startwith'),
    path('class/_find/',
         api_views.FindClassAPIView.as_view(), name='api-find_class'),
    path('backend/',
         api_views.BackendAPIView.as_view(), name='api-backend'),
    path('class/_similar/',
         api_views.MostSimilarAPIView.as_view(), name='api-find_class_similar'),
    path('sparql/',
         api_views.SparqlAPIView.as_view(), name='api-sparql'),
    path('dlquery/',
         api_views.DLQueryAPIView.as_view(), name='api-dlquery'),
    path('dlquery/logs/',
         api_views.DLQueryLogsDownloadAPIView.as_view(), name='api-dlquery_logs'),
    path('ontology/',
         api_views.ListOntologyAPIView.as_view(), name='api-list_ontologies'),
    path('ontology/_find/',
         api_views.FindOntologyAPIView.as_view(), name='api-find_ontology'),
    path('ontology/<str:acronym>/class/_matchsuperclasses/',
         api_views.MatchSuperClasses.as_view(), name='api-matach_super_class'),
    path('ontology/<str:acronym>/objectproperty/',
         api_views.ListOntologyObjectPropertiesView.as_view(), name='api-ontology_object_properties_list'),
    path('ontology/<str:acronym>/objectproperty/<path:property_iri>/',
         api_views.GetOntologyObjectPropertyView.as_view(), name='api-ontology_object_property_details'),
    path('ontology/<str:acronym>/class/<path:class_iri>/',
         api_views.GetOntologyClassView.as_view(), name='api-ontology_class_details'),
    path('ontology/<str:acronym>/root/<path:class_iri>/',
         api_views.FindOntologyRootClassView.as_view(), name='api-ontology_class_root'),
    path('instance/',
         api_views.ListInstanceAPIView.as_view(), name='api-instance_list'),
]
