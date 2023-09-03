import json
from unittest.mock import patch, Mock

from django.test import TestCase
from django.urls import reverse
from django.test import RequestFactory
from aberowl.views import MainView

from ..serializers import OntologySerializer

from aberowl.models import Ontology
from aberowl.tests.factories import OntologyFactory, SubmissionFactory
from requests.models import Response


class MainViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_main_view_renders_correct_template(self):
        request = self.factory.get(reverse('aberowl-main'))
        response = MainView.as_view()(request)
        self.assertEqual(response.status_code, 200)


class OntologyListViewTest(TestCase):
    def test_get_context_data(self):
        ontologies = OntologyFactory.create_batch(2, status=Ontology.CLASSIFIED, nb_servers=1)

        url = reverse('ontology-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected_data = OntologySerializer(ontologies, many=True).data
        expected_json = json.dumps(expected_data)

        self.assertJSONEqual(response.context['ontologies'], expected_json)


class OntologyDetailViewTest(TestCase):
    def setUp(self):
        self.ontology = OntologyFactory(acronym='TEST', name='Test Ontology')
        self.mock_response = Response()
        self.mock_response.status_code = 200
        self.mock_response.json = lambda: {
            "result": ["Class1", "Class2", "Class3"]
        }

    def test_ontology_detail_view_without_submission(self):
        url = reverse('ontology', kwargs={'onto': self.ontology.acronym})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    @patch('requests.get')
    @patch('aberowl.ont_server_request_processor.OntServerRequestProcessor.find_ontology_object_properties')
    def test_get_context_data(self, mock_properties, mock_classes):
        SubmissionFactory(ontology=self.ontology, version='1.0', date_released='2023-08-31')
        mock_response = Mock()
        mock_response.json.return_value = {'result': ['Class1', 'Class2']}
        mock_classes.return_value = mock_response
        mock_properties.return_value = {'result': ['Properties1', 'Properties2']}
        url = reverse('ontology', kwargs={'onto': 'TEST'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        context_data = json.loads(response.context['ontology'])
        self.assertEqual(context_data['classes'], ['Class1', 'Class2'])
        self.assertEqual(context_data['properties'], ['Properties1', 'Properties2'])

    @patch('requests.get')
    @patch('aberowl.ont_server_request_processor.OntServerRequestProcessor.find_ontology_object_properties')
    def test_get_context_data_404_error(self, mock_properties, mock_classes):
        SubmissionFactory(ontology=self.ontology, version='1.0', date_released='2023-08-31')
        mock_classes.side_effect = Exception('Mocked exception')
        mock_properties.side_effect = Exception()

        url = reverse('ontology', kwargs={'onto': 'TEST'})
        try:
            self.client.get(url)
        except Exception as e:
            self.assertEqual(str(e), 'Mocked exception')

    @patch('requests.get')
    @patch('aberowl.ont_server_request_processor.OntServerRequestProcessor.find_ontology_object_properties')
    def test_get_context_data_key_error(self, mock_properties, mock_classes):
        SubmissionFactory(ontology=self.ontology, version='1.0', date_released='2023-08-31')
        mock_response = Mock()
        mock_response.json.return_value = {'results': ['Class1', 'Class2']}
        mock_classes.return_value = mock_response
        mock_properties.return_value = {'results': ['Properties1', 'Properties2']}
        url = reverse('ontology', kwargs={'onto': 'TEST'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        context_data = json.loads(response.context['ontology'])
        self.assertEqual(context_data['name'], 'Test Ontology')
