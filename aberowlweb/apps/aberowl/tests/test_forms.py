from unittest.mock import Mock, patch

from django.core.files.uploadedfile import TemporaryUploadedFile
import tempfile
from django.test import TestCase
from aberowl.forms import OntologyForm, SubmissionForm
from aberowl.tests.factories import UserFactory, OntologyFactory, SubmissionFactory


def get_form_errors(form):
    error_messages = []
    for field, errors in form.errors.items():
        for error in errors:
            error_messages.append(error)
    return error_messages


class OntologyFormTest(TestCase):
    def setUp(self):
        self.user = UserFactory(username='testuser', password='testpassword')

    def test_form_valid_submission(self):
        form_data = {
            'acronym': 'TEST',
            'name': 'Test Ontology',
            'species': 'Test Species',
            'topics': 'Test Topics',
        }
        request = self.client.get('/ontology/create/')
        request.user = self.user
        form = OntologyForm(data=form_data, request=request)

        self.assertTrue(form.is_valid())

        ontology = form.save()

        self.assertEqual(ontology.acronym, 'TEST')
        self.assertEqual(ontology.name, 'Test Ontology')
        self.assertEqual(ontology.species, ['Test Species'])
        self.assertEqual(ontology.topics, ['Test Topics'])
        self.assertEqual(ontology.created_by, self.user)

    def test_form_valid_submission_with_instance(self):
        self.ontology = OntologyFactory(acronym='TEST', name='Test Ontology', created_by=self.user)
        form_data = {
            'acronym': 'TEST',
            'name': 'Test Ontology',
            'species': 'Test Species',
            'topics': 'Test Topics',
        }
        request = self.client.get('/ontology/create/')
        request.user = self.user
        form = OntologyForm(data=form_data, request=request, instance=self.ontology)
        self.assertTrue(form.is_valid())
        ontology = form.save()
        self.assertEqual(ontology.acronym, 'TEST')
        self.assertEqual(ontology.name, 'Test Ontology')
        self.assertEqual(ontology.species, ['Test Species'])
        self.assertEqual(ontology.topics, ['Test Topics'])
        self.assertEqual(ontology.created_by, self.user)

    def test_form_invalid_submission(self):
        form_data = {
            'acronym': '',  # Missing required field
            'name': 'Test Ontology',
            'species': 'Test Species',
            'topics': 'Test Topics',
        }

        form = OntologyForm(data=form_data, request=self.user)
        self.assertFalse(form.is_valid())


class SubmissionFormTest(TestCase):
    def setUp(self):
        self.user = UserFactory(username='testuser', password='testpassword')
        self.ontology = OntologyFactory(acronym='TEST',
                                        name='Test Ontology',
                                        species=['Test Species'],
                                        topics=['Test Topics'],
                                        created_by=self.user)
        self.submission = SubmissionFactory(ontology=self.ontology, version='1.0', date_released='2023-08-31')
        self.request = self.client.get('/test/')
        self.request.user = self.user

    @patch('aberowl.tasks.classify_ontology.delay')
    def test_form_submission(self, mock_delay):
        # when valid submission and classifiable is True
        mock_result = {'classifiable': True, 'other_key': 'other_value'}
        mock_delay.return_value = Mock(get=lambda: mock_result)
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"File content goes here")
        temp_file.seek(0)
        ontology_file = TemporaryUploadedFile(name="example.txt", content_type="text/plain", size=len(temp_file.read()),
                                              charset=None)
        form_data = {'version': '1.0', 'has_ontology_language': 'OWL'}
        form = SubmissionForm(data=form_data, request=self.request,
                              ontology=self.ontology, instance=self.submission, files={'ontology_file': ontology_file})
        self.assertTrue(form.is_valid())
        response_form_data = form.cleaned_data
        self.assertEqual(response_form_data['version'], form_data['version'])
        self.assertEqual(response_form_data['has_ontology_language'], form_data['has_ontology_language'])

        # when ontology_file and instance are missing
        form = SubmissionForm(data=form_data, request=self.request, ontology=self.ontology)
        self.assertFalse(form.is_valid())
        self.assertIn('ontology_file', form.errors)
        self.assertEqual(get_form_errors(form), ['Required when creating a submission!'])

        # when valid submission and classifiable is False
        mock_result = {'classifiable': False, 'other_key': 'other_value'}
        mock_delay.return_value = Mock(get=lambda: mock_result)
        form = SubmissionForm(data=form_data, request=self.request,
                              ontology=self.ontology, instance=self.submission, files={'ontology_file': ontology_file})
        self.assertFalse(form.is_valid())
        self.assertIn('ontology_file', form.errors)
        self.assertEqual(get_form_errors(form), ['Unloadable ontology file'])

    @patch('shutil.move')
    @patch('shutil.copy')
    @patch('os.chmod')
    @patch('aberowl.tasks.classify_ontology.delay')
    @patch('aberowl.tasks.index_submission.delay')
    @patch('aberowl.tasks.reload_ontology.delay')
    def test_save_new_submission(self, mock_reload_delay, mock_submission_delay, mock_classify_delay, mock_move, mock_copy, mock_chmod):
        mock_move.return_value, mock_copy.return_value, mock_chmod.return_value = None, None, None
        mock_result = {'classifiable': True, 'other_key': 'other_value', 'incon': 1, 'status': 2, 'nb_classes': 1,
                       'nb_individuals': 1,
                       'max_depth': 9, 'max_children': 0, 'avg_children': 8, 'nb_properties': 1}
        mock_submission_delay.return_value = Mock(get=lambda: mock_result)
        mock_classify_delay.return_value = Mock(get=lambda: mock_result)
        mock_reload_delay.return_value = Mock(get=lambda: mock_result)
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"File content goes here")
        temp_file.seek(0)
        ontology_file = TemporaryUploadedFile(name="example.txt", content_type="text/plain", size=len(temp_file.read()),
                                              charset=None)
        form_data = {
            'version': '1.0',
            'has_ontology_language': 'OWL'
        }

        form = SubmissionForm(data=form_data, request=self.request, ontology=self.ontology, instance=self.submission,
                              files={'ontology_file': ontology_file})
        self.assertTrue(form.is_valid())
        submission = form.save()
        self.assertEqual(submission.version, '1.0')
        self.assertEqual(submission.has_ontology_language, 'OWL')
        self.assertEqual(submission.ontology, self.ontology)

        form = SubmissionForm(data=form_data, request=self.request, ontology=self.ontology,
                              files={'ontology_file': ontology_file})
        self.assertTrue(form.is_valid())
        submission = form.save()
        self.assertEqual(submission.version, '1.0')
        self.assertEqual(submission.has_ontology_language, 'OWL')
        self.assertEqual(submission.ontology, self.ontology)
        self.assertEqual(submission.nb_inconsistent, mock_result['incon'])