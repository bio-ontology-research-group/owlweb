from unittest.mock import patch, Mock

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from aberowl.tests.factories import OntologyFactory


class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.query = 'example'
        self.ontology = 'sample_ontology'
        self.es_mock_response = {
            'hits': {
                'hits': [
                    {'_source': {'label': 'Example 1', 'embedding_vector': 10}},
                    {'_source': {'label': 'Example 2', 'embedding_vector': 20}}
                ]
            }
        }
        self.es_mock_response_empty = {'hits': {'hits': []}}


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
        self.assertEqual(response.data['result'], [{'label': 'Example 1', 'embedding_vector': 10},
                                                   {'label': 'Example 2', 'embedding_vector': 20}])


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
                           'script': 'runQuery.groovy', 'offset': '0', 'type': 'type1'}
        self.ontology_param = {'ontology': self.acronym}

    def get_mock_response(self):
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': [{'label': 'Example 1'}, {'label': 'Example 2'}],
            'total': 2,
        }
        return mock_response

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
        mock_get.return_value = self.get_mock_response()
        response = self.client.get(self.url, {**self.query_data, **self.ontology_param})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['total'], 2)

    @patch('requests.get')
    def test_get_when_nb_servers_is_zero(self, mock_get):
        self.ontology = self.get_ontology_obj(0)
        mock_get.return_value = self.get_mock_response()
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
        response = self.client.get(self.url, self.query_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['result'], [{'item1': 'value1'}, {'item2': 'value2'}])
        self.assertEqual(response.data['total'], 2)

    @patch('requests.get')
    def test_get_without_only_ontology_param_without_cache_with_ontology_data(self, mock_get):
        # # TODO: Need to fix the method and rewrite the test to pass with status 'ok'
        self.ontology = OntologyFactory(acronym=self.acronym, name='Test Ontology', nb_servers=2)
        mock_get.return_value = self.get_mock_response()
        response = self.client.get(self.url, self.query_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'That page number is less than 1')

    def test_get_without_only_ontology_param_without_cache_and_ontology_data(self):
        response = self.client.get(self.url, self.query_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'API server is down!')

    @patch('requests.get')
    def test_get_without_several_params(self, mock_get):
        self.ontology = self.get_ontology_obj(2)
        mock_get.return_value = self.get_mock_response()
        response = self.client.get(self.url, {'query': 'query'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['total'], 2)

    def test_get_without_several_params_with_ontology_data(self):
        response = self.client.get(self.url, {'query': 'query'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'exception')
        self.assertEqual(response.data['message'], 'API server is down!')
