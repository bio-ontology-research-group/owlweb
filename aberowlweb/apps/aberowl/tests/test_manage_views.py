from django.test import TestCase
from django.urls import reverse
from unittest.mock import Mock
from aberowl.manage_views import OntologyCreateView, OntologyUpdateView, SubmissionCreateView, SubmissionUpdateView
from aberowl.tests.factories import OntologyFactory, UserFactory, SubmissionFactory


class CommonTestCase(TestCase):
    def setUp(self):
        self.request = Mock()
        self.user = UserFactory(username='testu', password='testpassword')
        self.ontology = OntologyFactory(acronym='TEST', name='Test Ontology', created_by=self.user)
        self.submission = SubmissionFactory(ontology=self.ontology, version='1.0', date_released='2023-08-31')
        self.kwargs = {'onto_pk': self.ontology.pk}


class OntologyCreateViewTestCase(CommonTestCase):
    def test_get_success_url(self):
        view = OntologyCreateView()
        view.request = self.request
        view.object = self.ontology
        success_url = view.get_success_url()
        expected_url = reverse('create_submission', kwargs={'onto_pk': self.ontology.pk})
        self.assertEqual(success_url, expected_url)


class OntologyUpdateViewTestCase(CommonTestCase):
    def test_get_success_url(self):
        view = OntologyUpdateView()
        view.object = self.ontology
        success_url = view.get_success_url()
        expected_url = reverse('list_ontology')
        self.assertEqual(success_url, expected_url)


class SubmissionCreateViewTestCase(CommonTestCase):
    def test_get_success_url(self):
        view = SubmissionCreateView()
        view.kwargs = self.kwargs
        view.ontology = self.ontology
        success_url = view.get_success_url()
        expected_url = reverse('list_ontology')
        self.assertEqual(success_url, expected_url)


class SubmissionUpdateViewTestCase(CommonTestCase):
    def test_get_success_url(self):
        view = SubmissionUpdateView()
        view.kwargs = self.kwargs
        view.ontology = self.ontology
        success_url = view.get_success_url()
        expected_url = reverse('list_ontology')
        self.assertEqual(success_url, expected_url)
