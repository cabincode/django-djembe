# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Identity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('certificate', models.TextField(help_text='A PEM-encoded X.509 certificate.')),
                ('address', models.EmailField(help_text='If left blank, it will be extracted from the X.509 certificate.', max_length=256, blank=True)),
                ('key', models.TextField(help_text='If mail <em>from</em> this identity should be signed, put a PEM-encoded private key here. Make sure it does not require a passphrase.', blank=True)),
            ],
            options={
                'ordering': ['address'],
                'verbose_name_plural': 'Identities',
            },
            bases=(models.Model,),
        ),
    ]
