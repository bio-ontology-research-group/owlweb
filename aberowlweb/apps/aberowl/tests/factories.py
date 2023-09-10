from unittest.mock import Mock

import factory
from django.contrib.auth.models import User
from django.utils import timezone
from factory.django import DjangoModelFactory
from aberowl.models import Ontology, Submission
import pytz
from faker import Faker


def get_json_mock_response(data='test data', status_code=200):
    mock_response = Mock()
    mock_response.text = "This is the mock response content."
    mock_response.status_code = status_code
    mock_response.json.return_value = data
    return mock_response


fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')


class OntologyFactory(DjangoModelFactory):
    class Meta:
        model = Ontology

    acronym = factory.Sequence(lambda n: f'edam{n}')
    name = factory.Sequence(lambda n: f'Edam Ontology {n}')
    created_by = factory.SubFactory(UserFactory)
    source = Ontology.MANUAL
    date_created = timezone.now()
    status = Ontology.UNKNOWN
    topics = ['Topic 1', 'Topic 2']
    species = ['Species 1', 'Species 2']
    nb_servers = 0
    is_obsolete = False


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    ontology = factory.SubFactory(OntologyFactory)
    submission_id = factory.Faker('random_int')
    domain = fake.word()
    description = fake.text()
    documentation = fake.word()
    publication = fake.word()
    publications = []
    products = []
    taxon = {}
    date_released = fake.date_time(tzinfo=pytz.utc)
    date_created = fake.date_time(tzinfo=pytz.utc)
    home_page = fake.url()
    version = fake.text()
    has_ontology_language = factory.Iterator(
        Submission.LANGUAGE_CHOICES, getter=lambda c: c[0])
    nb_classes = factory.Faker('random_int')
    nb_individuals = factory.Faker('random_int')
    nb_properties = factory.Faker('random_int')
    max_depth = factory.Faker('random_int')
    max_children = factory.Faker('random_int')
    avg_children = factory.Faker('random_int')
    classifiable = factory.Faker('boolean')
    nb_inconsistent = factory.Faker('random_int')
    indexed = factory.Faker('boolean')
    md5sum = factory.Faker('md5')
