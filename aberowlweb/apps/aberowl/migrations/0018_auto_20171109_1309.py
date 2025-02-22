# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-09 13:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aberowl', '0017_ontology_nb_servers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ontology',
            name='is_running',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='port',
        ),
        migrations.RemoveField(
            model_name='ontology',
            name='server_ip',
        ),
        migrations.AlterField(
            model_name='submission',
            name='has_ontology_language',
            field=models.CharField(choices=[('OWL', 'OWL'), ('OBO', 'OBO'), ('SKOS', 'SKOS'), ('UMLS', 'UMLS')],
                                   max_length=15, verbose_name='Ontology Language'),
        ),
    ]
