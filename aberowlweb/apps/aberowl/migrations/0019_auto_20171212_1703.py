from __future__ import unicode_literals
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('aberowl', '0018_auto_20171109_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='ontology',
            name='is_obsolete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ontology',
            name='source',
            field=models.CharField(default='manual', max_length=15),
        ),
        migrations.AddField(
            model_name='submission',
            name='domain',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='md5sum',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='products',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='publications',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='taxon',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('ontology', 'md5sum'), ('ontology', 'submission_id')]),
        ),
    ]
