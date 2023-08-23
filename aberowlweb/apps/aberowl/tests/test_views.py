import json
from django.test import TestCase
from django.urls import reverse
from django.test import RequestFactory
from aberowl.views import MainView

from ..serializers import OntologySerializer

from aberowl.models import Ontology
from aberowl.tests.factories import OntologyFactory
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
        self.ontology = OntologyFactory()
        self.mock_response = Response()
        self.mock_response.status_code = 200
        self.mock_response.json = lambda: {
            "result": ["Class1", "Class2", "Class3"]
        }

    def test_ontology_detail_view_without_submission(self):
        url = reverse('ontology', kwargs={'onto': self.ontology.acronym})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
