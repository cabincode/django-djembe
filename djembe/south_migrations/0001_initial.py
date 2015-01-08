# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Identity'
        db.create_table('djembe_identity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.EmailField')(max_length=256, blank=True)),
            ('certificate', self.gf('django.db.models.fields.TextField')()),
            ('key', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('djembe', ['Identity'])


    def backwards(self, orm):
        # Deleting model 'Identity'
        db.delete_table('djembe_identity')


    models = {
        'djembe.identity': {
            'Meta': {'ordering': "['address']", 'object_name': 'Identity'},
            'address': ('django.db.models.fields.EmailField', [], {'max_length': '256', 'blank': 'True'}),
            'certificate': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['djembe']