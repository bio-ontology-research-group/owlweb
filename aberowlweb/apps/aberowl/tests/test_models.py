from django.test import TestCase
from .factories import OntologyFactory, UserFactory, SubmissionFactory
from aberowl.models import ABEROWL_API_URL


class OntologySubmissionTestCase(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.ontology = OntologyFactory(created_by=self.user)
        self.submission = SubmissionFactory(ontology=self.ontology)

    def test_ontology_creation(self):
        self.assertEqual(self.ontology.acronym, "edam2")
        self.assertEqual(self.ontology.name, "Edam Ontology 2")

    def test_get_latest_submission(self):
        latest_submission = self.ontology.get_latest_submission()
        self.assertEqual(latest_submission, self.submission)

    def test_ontology_api_url(self):
        self.assertEqual(self.ontology.get_api_url(), ABEROWL_API_URL)

    def test_ontology_str(self):
        self.assertEqual(self.ontology.__str__(), self.ontology.acronym + ' - ' + self.ontology.name)

    def test_submission_str(self):
        self.assertEqual(self.submission.__str__(),
                         str(self.submission.ontology) + ' - ' + str(self.submission.submission_id))

    def test_submission_filepath(self):
        self.assertEqual(self.submission.get_filepath(),
                         f'media/ontologies/{self.submission.ontology.acronym}/{self.submission.submission_id}/{self.submission.ontology.acronym}.owl')
