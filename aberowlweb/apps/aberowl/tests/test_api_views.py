from unittest.mock import patch, Mock
from urllib.parse import urlencode

from django.http import HttpResponse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

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


class FindClassByMethodStartWithAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = '/api/class/_startwith/'

    @patch('aberowl.api_views.search')
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

    @patch('aberowl.api_views.search')
    def test_get_with_exception(self, mock_search):
        mock_search.side_effect = Exception('Mocked exception')
        response = self.client.get(self.url, {'query': self.query, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'Mocked exception')


class FindClassAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = '/api/class/_find/'

    @patch('aberowl.api_views.search')
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

    @patch('aberowl.api_views.search')
    def test_get_with_missing_ontology(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'query': self.query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], [item['_source'] for item in self.es_mock_response['hits']['hits']])


class MostSimilarAPIViewTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.url = '/api/class/_similar/'
        self.cls = 'example_class'
        self.size = '10'

    @patch('aberowl.api_views.search')
    def test_get_with_valid_parameters(self, mock_search):
        mock_search.return_value = self.es_mock_response
        response = self.client.get(self.url, {'class': self.cls, 'size': self.size, 'ontology': self.ontology})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    @patch('aberowl.api_views.search')
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
        self.url = '/api/backend/'
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
        mock_page.page.return_value.object_list = [{'item1': 'value1'}, {'item2': 'value2'}]
        mock_page.count = 2
        mock_page_cache.return_value = mock_page
        response = self.client.get(self.url, {**self.query_data, 'type': 'type1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], [{'item1': 'value1'}, {'item2': 'value2'}])
        self.assertEqual(response.data['total'], 2)

    @patch('requests.get')
    def test_get_without_only_ontology_param_without_cache_with_ontology_data(self, mock_get):
        # # TODO: Need to fix the method and rewrite the test to pass with status 'ok'
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
        self.url = '/api/ontology/_find/'

    @patch('aberowl.api_views.search')
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
        self.query = 'SELECT * WHERE {?s ?p ?o}'
        self.format = 'json'
        self.url = '/api/sparql/'

    @patch('aberowl.api_views.SparqlAPIView.process_query')
    def test_post_with_valid_data(self, mock_process_query):
        mock_process_query.return_value = HttpResponse()
        response = self.client.post(self.url, {'query': self.query, 'format': self.format})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('aberowl.api_views.SparqlAPIView.process_query')
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
