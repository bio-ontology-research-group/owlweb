from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.query = 'example'
        self.ontology = 'sample_ontology'
        self.es_mock_response = {
            'hits': {
                'hits': [
                    {'_source': {'label': 'Example 1'}},
                    {'_source': {'label': 'Example 2'}}
                ]
            }
        }


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
        self.assertEqual(response.data['result'], [{'label': 'Example 1'}, {'label': 'Example 2'}])
