from enum import Enum

from aberowl.models import Ontology

from django.conf import settings

import requests
import urllib
import logging

logger = logging.getLogger(__name__)


class RequestType(Enum):
    DL_QUERY = "runQuery.groovy"
    FIND_ROOT = "findRoot.groovy"
    FIND_OBJ_PROPS = "getObjectProperties.groovy"
    FIND_INSTANCES = "findInstances.groovy"


class OntServerRequestProcessor:
    ABEROWL_API_URL = getattr(settings, 'ABEROWL_API_URL', 'http://localhost:8080/api/')

    def find_ontology_root(self, owl_class, ontology_acronym):
        ontology = self.__load_ontology(ontology_acronym)
        url = ontology.get_api_url()
        query_string = 'query=' + owl_class + '&ontology=' + ontology_acronym
        return self.__execute_request(url, RequestType.FIND_ROOT.value, query_string)

    def find_ontology_object_properties(self, ontology_acronym, ont_property=None):
        ontology = self.__load_ontology(ontology_acronym)
        url = ontology.get_api_url()
        query_string = {'ontology': ontology_acronym}
        if ont_property:
            query_string['property'] = ont_property
        return self.__execute_request(url, RequestType.FIND_OBJ_PROPS.value, urllib.parse.urlencode(query_string))

    def match_superclasses(self, source_classes, target_classes, ontology):
        supercls_map = {}
        for source_cls in source_classes:
            result = self.execute_dl_query(f'<{source_cls}>', 'superclass', ontology, axioms=False, labels=False,
                                           direct=False)
            for supercls in result['result']:
                if supercls['owlClass'] in supercls_map:
                    continue

                supercls_map[supercls['owlClass']] = supercls

        for target_cls in target_classes:
            result = self.execute_dl_query(f'<{target_cls}>', 'superclass', ontology, axioms=False, labels=False,
                                           direct=False)
            for supercls in result['result']:
                if supercls['owlClass'] in supercls_map:
                    continue

                supercls_map[supercls['owlClass']] = supercls

        for key in list(supercls_map):
            result = self.execute_dl_query(key, 'superclass', ontology, axioms=False, labels=False, direct=False)
            for supercls in result['result']:
                if supercls['owlClass'] in supercls_map:
                    del supercls_map[supercls['owlClass']]

        return {'result': supercls_map.values()}

    def find_by_ontology_and_class(self, ontology_acronym, class_iri):
        ontology = self.__load_ontology(ontology_acronym)
        url = ontology.get_api_url()
        query_string = {'ontology': ontology_acronym, 'class_iri': class_iri}
        return self.__execute_request(url, RequestType.FIND_INSTANCES.value, urllib.parse.urlencode(query_string))

    def execute_dl_query(self, query, query_type, ontology_acronym=None, axioms=None, labels=None, direct=None):
        url = None
        if labels:
            query = query.lower()
        query_string = {'query': query, 'type': query_type, 'axioms': axioms, 'labels': labels, 'direct': direct}
        if ontology_acronym is not None:
            queryset = Ontology.objects.filter(acronym=ontology_acronym)
            if queryset.exists():
                ontology = queryset.get()
                if ontology.nb_servers:
                    url = ontology.get_api_url()
                    query_string['ontology'] = ontology_acronym
                else:
                    raise Exception('API server is down!')
            else:
                raise Exception(
                    "Ontology \'{ontology_acronym}\' does not exist".format(ontology_acronym=ontology_acronym))

        else:
            queryset = Ontology.objects.filter(nb_servers__gt=0)
            if not queryset.exists():
                raise Exception('API server is down!')

            url = self.ABEROWL_API_URL

        return self.__execute_request(url, RequestType.DL_QUERY.value, urllib.parse.urlencode(query_string))

    def __load_ontology(self, ontology_acronym):
        if ontology_acronym is not None:
            queryset = Ontology.objects.filter(acronym=ontology_acronym)
            if not queryset.exists():
                raise Exception(
                    "Ontology \'{ontology_acronym}\' does not exist".format(ontology_acronym=ontology_acronym))

            ontology = queryset.get()
            if not ontology.nb_servers:
                raise Exception('API server is down!')

            return ontology

    def __execute_request(self, base_url, request_type, query_string):
        url = "{base_url}{request_type}?{query_string}".format(base_url=base_url, request_type=request_type,
                                                               query_string=query_string)
        logger.info("Executing request on Ontology Server:" + url)
        response = requests.get(url)
        return response.json()
