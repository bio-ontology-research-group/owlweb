from unittest.mock import patch, Mock, mock_open
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from aberowl.models import Ontology
from aberowl import api_views

from aberowl.tests.factories import OntologyFactory


def get_json_mock_response(data, status_code=200):
    mock_response = Mock()
    mock_response.text = "This is the mock response content."
    mock_response.status_code = status_code
    mock_response.json.return_value = data
    return mock_response


class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.query = 'SELECT * WHERE {?s ?p ?o}'
        self.format = 'json'
        self.endpoint = 'https://example.com/sparql'
        self.ontology = 'sample_ontology'
        self.es_mock_response = {
            'hits': {
                'hits': [
                    {'_source': {'label': 'Example 1', 'embedding_vector': 10, 'name': 'Name 1'}},
                    {'_source': {'label': 'Example 2', 'embedding_vector': 20, 'name': 'Name 2'}}
                ]
            }
        }
        self.es_mock_response_empty = {'hits': {'hits': []}}
        self.mock_result = {'result': [{'label': 'Example 1'}, {'label': 'Example 2'}], 'total': 2, }


class ApiViewMethodsTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = 'https://example.com/api/data'

    @patch('requests.get')
    def test_make_request_success(self, mock_get):
        mock_get.return_value = get_json_mock_response(data=self.mock_result)
        result = api_views.make_request(self.url)
        mock_get.assert_called_once_with(self.url, timeout=2)
        self.assertEqual(result, self.mock_result['result'])

    @patch('requests.get')
    def test_make_request_failure(self, mock_get):
        mock_get.side_effect = Exception('Mocked exception')
        result = api_views.make_request(self.url)
        mock_get.assert_called_once_with(self.url, timeout=2)
        self.assertEqual(result, [])

    @patch.object(api_views.es, 'search')
    def test_search_success(self, mock_search):
        mock_search.return_value = self.es_mock_response
        index_name = 'test_index'
        query_data = {'query': {'match_all': {}}}
        result = api_views.search(index_name, query_data)
        mock_search.assert_called_once_with(index=index_name, body=query_data, request_timeout=15)
        self.assertEqual(result, self.es_mock_response)

    @patch.object(api_views.es, 'search')
    def test_search_failure(self, mock_search):
        mock_search.side_effect = Exception('Mocked Elasticsearch exception')
        index_name = 'test_index'
        query_data = {'query': {'match_all': {}}}
        result = api_views.search(index_name, query_data)
        mock_search.assert_called_once_with(index=index_name, body=query_data, request_timeout=15)
        self.assertEqual(result, {'hits': {'hits': []}})

    def test_fix_iri_path_param(self):
        # http
        iri = 'http://example.com/resource'
        fixed_iri = api_views.fix_iri_path_param(iri)
        self.assertEqual(fixed_iri, 'http://example.com/resource')

        # https
        iri = 'https://example.com/resource'
        fixed_iri = api_views.fix_iri_path_param(iri)
        self.assertEqual(fixed_iri, 'https://example.com/resource')

        # mixed_http
        iri = 'http:/example.com/resource'
        fixed_iri = api_views.fix_iri_path_param(iri)
        self.assertEqual(fixed_iri, 'http://example.com/resource')

        # mixed_https
        iri = 'https:/example.com/resource'
        fixed_iri = api_views.fix_iri_path_param(iri)
        self.assertEqual(fixed_iri, 'https://example.com/resource')

        # no_change
        iri = 'https://example.com/resource'
        fixed_iri = api_views.fix_iri_path_param(iri)
        self.assertEqual(fixed_iri, 'https://example.com/resource')


class FindClassByMethodStartWithAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-find_class_startwith')

    @patch.object(api_views, 'search')
    def test_get_with_valid_query_and_ontology(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'query': self.query, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    def test_get_with_missing_query(self):
        response = self.client.get(self.url, {'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'query is required')

    def test_get_with_missing_ontology(self):
        response = self.client.get(self.url, {'query': self.query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'ontology is required')

    @patch.object(api_views, 'search')
    def test_get_with_exception(self, mock_search):
        mock_search.side_effect = Exception('Mocked exception')
        response = self.client.get(self.url, {'query': self.query, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'Mocked exception')


class FindClassAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-find_class')

    @patch.object(api_views, 'search')
    def test_get_with_valid_query(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'query': self.query, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    def test_get_with_missing_query(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Please provide query parameter!')

    @patch.object(api_views, 'search')
    def test_get_with_missing_ontology(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'query': self.query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], [item['_source'] for item in self.es_mock_response['hits']['hits']])


class MostSimilarAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-find_class_similar')
        self.cls = 'example_class'
        self.size = '10'

    @patch.object(api_views, 'search')
    def test_get_with_valid_parameters(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'class': self.cls, 'size': self.size, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    @patch.object(api_views, 'search')
    def test_get_with_es_empty_response(self, mock_search):
        mock_search.return_value = self.es_mock_response_empty
        response = self.client.get(self.url, {'class': self.cls, 'size': self.size, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'not found')

    def test_get_with_missing_class_parameter(self):
        response = self.client.get(self.url, {'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'class is required')

    def test_get_with_missing_ontology_parameter(self):
        response = self.client.get(self.url, {'class': self.cls, 'size': self.size})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'ontology is required')

    def test_get_with_invalid_size_parameter(self):
        response = self.client.get(self.url,
                                   {'class': self.cls, 'ontology': self.ontology, 'size': 'invalid'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'invalid literal for int() with base 10: \'invalid\'')


class BackendAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-backend')
        self.acronym = 'TEST'
        self.query_data = {'query': 'query=example&type=test&ontology=sample&script=script&offset=0',
                           'script': 'runQuery.groovy', 'offset': '0'}
        self.ontology_param = {'ontology': self.acronym}

    def get_ontology_obj(self, nb_servers):
        return OntologyFactory(acronym=self.acronym, name='Test Ontology', nb_servers=nb_servers)

    def test_get_with_missing_script_parameter(self):
        response = self.client.get(self.url, {'query': 'example'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'script is required')

    @patch('requests.get')
    def test_get_with_valid_parameters(self, mock_get):
        self.ontology = self.get_ontology_obj(2)
        mock_get.return_value = get_json_mock_response(self.mock_result)
        response = self.client.get(self.url, {**self.query_data, **self.ontology_param})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['total'], 2)

    @patch('requests.get')
    def test_get_when_nb_servers_is_zero(self, mock_get):
        self.ontology = self.get_ontology_obj(0)
        mock_get.return_value = get_json_mock_response(self.mock_result)
        response = self.client.get(self.url, {**self.query_data, **self.ontology_param})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'API server is down!')

    def test_get_with_ontology_param_without_ontology_data(self):
        response = self.client.get(self.url, {**self.query_data, **self.ontology_param})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'Ontology does not exist!')

    @patch('expiringdict.ExpiringDict.get')
    def test_get_without_only_ontology_param_with_cache(self, mock_page_cache):
        mock_page = Mock()
        mock_page.page.return_value.object_list = self.mock_result['result']
        mock_page.count = 2
        mock_page_cache.return_value = mock_page
        response = self.client.get(self.url, {**self.query_data, 'type': 'type1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], self.mock_result['result'])
        self.assertEqual(response.data['total'], 2)

    @patch('requests.get')
    def test_get_without_only_ontology_param_without_cache_with_ontology_data(self, mock_get):
        # TODO: Need to fix the method and rewrite the test to pass with status 'ok'
        self.ontology = OntologyFactory(acronym=self.acronym, name='Test Ontology', nb_servers=2)
        mock_get.return_value = get_json_mock_response(self.mock_result)
        response = self.client.get(self.url, {**self.query_data, 'type': 'type1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'That page number is less than 1')

    def test_get_without_only_ontology_param_without_cache_and_ontology_data(self):
        response = self.client.get(self.url, {**self.query_data, 'type': 'type1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'API server is down!')

    @patch('requests.get')
    def test_get_without_several_params(self, mock_get):
        self.ontology = self.get_ontology_obj(2)
        mock_get.return_value = get_json_mock_response(self.mock_result)
        response = self.client.get(self.url, self.query_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['total'], 2)

    def test_get_without_several_params_without_ontology_data(self):
        response = self.client.get(self.url, self.query_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'API server is down!')


class FindOntologyAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-find_ontology')

    @patch.object(api_views, 'search')
    def test_get_with_valid_query(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'query': 'example'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [item['_source'] for item in self.es_mock_response['hits']['hits']])

    def test_get_with_missing_query(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'query field is required')


class SparqlAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-sparql')

    @patch.object(api_views.SparqlAPIView, 'process_query')
    def test_post_with_valid_data(self, mock_process_query):
        mock_process_query.return_value = HttpResponse()
        response = self.client.post(self.url, {'query': self.query, 'format': self.format})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch.object(api_views.SparqlAPIView, 'process_query')
    def test_get_with_valid_query(self, mock_process_query):
        # TODO need to fix code and rewrite the test for missing format and exceptions
        mock_process_query.return_value = HttpResponse()
        response = self.client.get(self.url, {'query': self.query, 'format': self.format, 'result_format': self.format})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('requests.get')
    def test_process_query(self, mock_get):
        mock_get.return_value = get_json_mock_response(data={'query': self.query, 'endpoint': self.endpoint})
        from aberowl.api_views import SparqlAPIView
        view = SparqlAPIView()
        query_url = urlencode(
            {'query': self.query, 'format': 'json', 'timeout': 0, 'debug': 'on', 'run': 'Run Query', }, doseq=True)

        # when ispost is True
        response = view.process_query(query='query', res_format='json', ispost=True)
        self.assertEqual(response['Location'], f'{self.endpoint}?{query_url}')

        # when ispost is False (default)
        response = view.process_query(query='query', res_format='json')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'{self.endpoint}?{query_url}')

        # when query is missing
        response = view.process_query(query=None, res_format='json', ispost=True)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'query is required')

        # when res_format is missing
        response = view.process_query(query='query', res_format=None, ispost=True)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'result format is required')

        # when requests.get responds status code 400
        mock_get.return_value = get_json_mock_response(data={'query': self.query, 'endpoint': self.endpoint},
                                                       status_code=400)
        response = view.process_query(query='query', res_format='json', ispost=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'This is the mock response content.')

        # when exception occurs
        mock_get.side_effect = Exception('Mocked exception')
        response = view.process_query(query='query', res_format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'Mocked exception')


class DLQueryAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-dlquery')

    @patch.object(api_views.ont_server, 'execute_dl_query')
    @patch('expiringdict.ExpiringDict.get')
    def test_get_with_valid_data(self, mock_page_cache, mock_execute_dl_query):
        mock_page = Mock()
        mock_page.page.return_value.object_list = self.mock_result['result']
        mock_page.count = 2
        mock_page_cache.return_value = mock_page
        mock_execute_dl_query.return_value = self.mock_result

        # when all params are expected
        response = self.client.get(self.url, {'query': self.query, 'type': self.query, 'offset': 2,
                                              'format': self.format})
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], self.mock_result['result'])
        self.assertEqual(response.data['total'], 2)

        # when query is missing
        response = self.client.get(self.url, {'format': self.format})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'query is required')

        # when type is missing
        response = self.client.get(self.url, {'query': self.query, 'format': self.format})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'type is required')

        # when offset is missing
        response = self.client.get(self.url, {'query': self.query, 'type': self.query, 'format': self.format})
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['result'], self.mock_result['result'])

        # when cache is empty
        # TODO: Need to fix the method and rewrite the test to pass with status 'ok'
        mock_page_cache.return_value = None
        response = self.client.get(self.url, {'query': self.query, 'type': self.query, 'offset': 2,
                                              'format': self.format})
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], "'NoneType' object has no attribute 'page'")

        # when exception occurs
        mock_page_cache.side_effect = Exception('Mocked exception')
        response = self.client.get(self.url, {'query': self.query, 'type': self.query, 'offset': 2,
                                              'format': self.format})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'Mocked exception')


LOG_FOLDER = getattr(
    settings, 'DLQUERY_LOGS_FOLDER', 'dl')


class DLQueryLogsDownloadAPIViewTest(APITestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('api-dlquery_logs')

    @patch('builtins.open', mock_open(read_data='Mocked log data'), create=True)
    def test_get_with_existing_log_file(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response.content.decode(), 'Mocked log data')

    @patch('builtins.open')
    def test_get_with_nonexistent_log_file(self, mock_open_method):
        mock_open_method.side_effect = FileNotFoundError
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class ListOntologyObjectPropertiesViewTest(APITestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('api-ontology_object_properties_list', args=['ontology_acronym'])

    @patch.object(api_views.ont_server, 'find_ontology_object_properties')
    def test_get_with_valid_data(self, mock_find_ontology_object_properties):
        mock_find_ontology_object_properties.return_value = self.mock_result
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {**self.mock_result, 'status': 'ok', 'total': 2}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views.ont_server, 'find_ontology_object_properties')
    def test_get_with_exception(self, mock_find_ontology_object_properties):
        mock_find_ontology_object_properties.side_effect = Exception('Mocked exception')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Mocked exception'}
        self.assertDictEqual(response.data, expected_response_data)


class GetOntologyObjectPropertyViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-ontology_object_property_details', args=['ontology_acronym', 'property_iri'])

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'find_ontology_object_properties')
    def test_get_with_valid_data(self, mock_find_ontology_object_properties, mock_fix_iri_path_param):
        mock_fix_iri_path_param.return_value = 'mocked_property_iri'
        mock_find_ontology_object_properties.return_value = self.mock_result
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {**self.mock_result, 'status': 'ok'}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'find_ontology_object_properties')
    def test_get_with_exception(self, mock_find_ontology_object_properties, mock_fix_iri_path_param):
        mock_find_ontology_object_properties.side_effect = Exception('Mocked exception')
        mock_fix_iri_path_param.return_value = 'mocked_property_iri'
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Mocked exception'}
        self.assertDictEqual(response.data, expected_response_data)


class GetOntologyClassViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('api-ontology_class_details', args=['ontology_acronym', 'class_iri'])

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'execute_dl_query')
    @patch.object(Ontology.objects, 'filter')
    def test_get_and_post_with_valid_data(self, mock_filter, mock_execute_dl_query, mock_fix_iri_path_param):
        mock_fix_iri_path_param.return_value = 'mocked_class_iri'
        mock_ontology = Ontology(acronym='ontology_acronym', nb_servers=True)
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.get.return_value = mock_ontology
        mock_execute_dl_query.return_value = self.mock_result
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {**self.mock_result, 'status': 'ok'}
        self.assertDictEqual(response.data, expected_response_data)

        # test post request
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {**self.mock_result, 'status': 'ok'}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(Ontology.objects, 'filter')
    def test_get_with_nonexistent_ontology(self, mock_filter, mock_fix_iri_path_param):
        mock_fix_iri_path_param.return_value = 'mocked_class_iri'
        mock_filter.return_value.exists.return_value = False
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Ontology does not exist!'}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'execute_dl_query')
    @patch.object(Ontology.objects, 'filter')
    def test_get_with_exception(self, mock_filter, mock_execute_dl_query, mock_fix_iri_path_param):
        mock_execute_dl_query.side_effect = Exception('Mocked exception')
        mock_fix_iri_path_param.return_value = 'mocked_class_iri'
        mock_ontology = Ontology(acronym='ontology_acronym', nb_servers=0)
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.get.return_value = mock_ontology
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'API server is down!'}
        self.assertDictEqual(response.data, expected_response_data)


class FindOntologyRootClassViewTest(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse('api-ontology_class_root', args=['ontology_acronym', 'class_iri'])

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'find_ontology_root')
    def test_get_with_valid_data(self, mock_find_ontology_root, mock_fix_iri_path_param):
        mock_find_ontology_root.return_value = self.mock_result
        mock_fix_iri_path_param.return_value = 'mocked_class_iri'
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {**self.mock_result, 'status': 'ok', 'total': 2}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views, 'fix_iri_path_param')
    @patch.object(api_views.ont_server, 'find_ontology_root')
    def test_get_with_exception(self, mock_find_ontology_root, mock_fix_iri_path_param):
        mock_find_ontology_root.side_effect = Exception('Mocked exception')
        mock_fix_iri_path_param.return_value = 'mocked_class_iri'
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Mocked exception'}
        self.assertDictEqual(response.data, expected_response_data)


class ListInstanceAPIViewTest(APITestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('api-instance_list')

    @patch.object(api_views.ont_server, 'find_by_ontology_and_class')
    def test_get_with_valid_data(self, mock_find_by_ontology_and_class):
        mock_find_by_ontology_and_class.return_value = self.mock_result
        response = self.client.get(self.url, {'ontology': self.ontology, 'class_iri': 'class_iri_value'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = self.mock_result
        self.assertDictEqual(response.data, expected_response_data)

    def test_get_with_missing_ontology(self):
        response = self.client.get(self.url, {'class_iri': 'class_iri_value'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'error', 'message': 'ontology acronym is required'}
        self.assertDictEqual(response.data, expected_response_data)

    def test_get_with_missing_class_iri(self):
        response = self.client.get(self.url, {'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'error', 'message': 'class_iri is required'}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views.ont_server, 'find_by_ontology_and_class')
    def test_get_with_exception(self, mock_find_by_ontology_and_class):
        mock_find_by_ontology_and_class.side_effect = Exception('Mocked exception')
        response = self.client.get(self.url, {'ontology': self.ontology, 'class_iri': 'class_iri_value'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Mocked exception'}
        self.assertDictEqual(response.data, expected_response_data)


class MatchSuperClassesTest(APITestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse('api-matach_super_class', args=['ontology_acronym'])

    @patch.object(api_views.ont_server, 'match_superclasses')
    def test_post_with_valid_data(self, mock_match_superclasses):
        mock_match_superclasses.return_value = self.mock_result
        data = {'source_classes': ['class1', 'class2'], 'target_classes': ['class3', 'class4']}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = self.mock_result
        self.assertDictEqual(response.data, expected_response_data)

    def test_post_with_missing_source_classes(self):
        data = {'target_classes': ['class3', 'class4']}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': "'source_classes' element is required"}
        self.assertDictEqual(response.data, expected_response_data)

    def test_post_with_missing_target_classes(self):
        data = {'source_classes': ['class1', 'class2']}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': "'target_classes' element is required"}
        self.assertDictEqual(response.data, expected_response_data)

    @patch.object(api_views.ont_server, 'match_superclasses')
    def test_post_with_exception(self, mock_match_superclasses):
        mock_match_superclasses.side_effect = Exception('Mocked exception')
        data = {'source_classes': ['class1', 'class2'], 'target_classes': ['class3', 'class4']}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response_data = {'status': 'exception', 'message': 'Mocked exception'}
        self.assertDictEqual(response.data, expected_response_data)
