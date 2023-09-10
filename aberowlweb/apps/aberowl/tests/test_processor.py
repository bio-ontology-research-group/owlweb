from django.test import TestCase
from unittest.mock import patch
from aberowl.ont_server_request_processor import OntServerRequestProcessor
from aberowl.tests.factories import OntologyFactory, get_json_mock_response

processor = OntServerRequestProcessor()


class TestOntServerRequestProcessor(TestCase):
    @patch('requests.get')
    def test_find_ontology_root(self, mock_get):
        OntologyFactory(acronym='TEST', nb_servers=2), OntologyFactory(acronym='TEST1', nb_servers=0)
        mock_get.return_value = get_json_mock_response('test')
        result = processor.find_ontology_root('owl_class', 'TEST')
        self.assertEqual(result, 'test')
        try:
            result = processor.find_ontology_root('owl_class', 'TEST2')
            self.assertEqual(result, 'test')
        except Exception as e:
            expected_message = "Ontology 'TEST2' does not exist"
            self.assertEqual(str(e), expected_message)
        try:
            result = processor.find_ontology_root('owl_class', 'TEST1')
            self.assertEqual(result, 'test')
        except Exception as e:
            expected_message = "API server is down!"
            self.assertEqual(str(e), expected_message)

    @patch('requests.get')
    def test_find_ontology_object_properties(self, mock_get):
        OntologyFactory(acronym='TEST', nb_servers=2)
        mock_get.return_value = get_json_mock_response('test')
        result = processor.find_ontology_object_properties('TEST', ont_property='property')
        self.assertEqual(result, 'test')

    @patch.object(processor, 'execute_dl_query')
    @patch('requests.get')
    def test_match_superclasses(self, mock_get, mock_execute_dl_query):
        OntologyFactory(acronym='TEST', nb_servers=2)
        mock_get.return_value = get_json_mock_response('test')
        mock_response1 = {'result': [{'owlClass': 'Class1'}, {'owlClass': 'Class2'}, {'owlClass': 'Class1'}]}
        mock_response2 = {'result': [{'owlClass': 'Class3'}, {'owlClass': 'Class4'}, {'owlClass': 'Class3'}]}
        mock_response3 = {'result': [{'owlClass': 'Class2'}, {'owlClass': 'Class3'}]}
        mock_execute_dl_query.side_effect = [mock_response1, mock_response2, mock_response3, mock_response3,
                                             mock_response3, mock_response3]

        source_classes = ['Class1']
        target_classes = ['Class3']
        ontology = 'TEST'

        result = processor.match_superclasses(source_classes, target_classes, ontology)

        self.assertEqual(len(result['result']), 2)
        self.assertIn({'owlClass': 'Class1'}, result['result'])
        self.assertIn({'owlClass': 'Class4'}, result['result'])

    @patch('requests.get')
    def test_find_by_ontology_and_class(self, mock_get):
        OntologyFactory(acronym='TEST', nb_servers=2)
        mock_get.return_value = get_json_mock_response('test')
        result = processor.find_by_ontology_and_class('TEST', 'test_class')
        self.assertEqual(result, 'test')

    @patch('requests.get')
    def test_execute_dl_query(self, mock_get):
        OntologyFactory(acronym='TEST1', nb_servers=0)
        try:
            processor.execute_dl_query(query='query', query_type='query_type', ontology_acronym=None, labels=True)
        except Exception as e:
            expected_message = "API server is down!"
            self.assertEqual(str(e), expected_message)

        OntologyFactory(acronym='TEST', nb_servers=2)
        mock_get.return_value = get_json_mock_response('test')
        result = processor.execute_dl_query(query='query', query_type='query_type', ontology_acronym=None, labels=True)
        self.assertEqual(result, 'test')

        result = processor.execute_dl_query(query='query', query_type='query_type', ontology_acronym='TEST',
                                            labels=True)
        self.assertEqual(result, 'test')

        try:
            processor.execute_dl_query(query='query', query_type='query_type', ontology_acronym='TEST2', labels=True)
        except Exception as e:
            self.assertEqual(str(e), "Ontology 'TEST2' does not exist")

        try:
            processor.execute_dl_query(query='query', query_type='query_type', ontology_acronym='TEST1', labels=True)
        except Exception as e:
            self.assertEqual(str(e), "API server is down!")

    def test_is_query_complex(self):
        from aberowl.dl_query_logger import is_query_complex
        self.assertFalse(is_query_complex(None))
        self.assertFalse(is_query_complex('  '))
        self.assertTrue(is_query_complex('query test'))
        self.assertTrue(is_query_complex("'test' query"))
        self.assertFalse(is_query_complex("test' query"))
