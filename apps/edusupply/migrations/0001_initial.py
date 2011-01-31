# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Country'
        db.create_table('edusupply_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('edusupply', ['Country'])

        # Adding model 'Province'
        db.create_table('edusupply_province', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('edusupply', ['Province'])

        # Adding model 'District'
        db.create_table('edusupply_district', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=20, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
        ))
        db.send_create_signal('edusupply', ['District'])

        # Adding model 'School'
        db.create_table('edusupply_school', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Point'], null=True, blank=True)),
            ('parent_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('km_to_DEO', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=20, null=True, blank=True)),
            ('satellite_number', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=20, null=True, blank=True)),
            ('total_enrollment', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=20, null=True, blank=True)),
            ('level', self.gf('django.db.models.fields.CharField')(default='U', max_length=2)),
            ('form_number', self.gf('django.db.models.fields.CharField')(max_length=160, null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=8, null=True, blank=True)),
        ))
        db.send_create_signal('edusupply', ['School'])


    def backwards(self, orm):
        
        # Deleting model 'Country'
        db.delete_table('edusupply_country')

        # Deleting model 'Province'
        db.delete_table('edusupply_province')

        # Deleting model 'District'
        db.delete_table('edusupply_district')

        # Deleting model 'School'
        db.delete_table('edusupply_school')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'edusupply.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'edusupply.district': {
            'Meta': {'object_name': 'District'},
            'code': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'edusupply.province': {
            'Meta': {'object_name': 'Province'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'edusupply.school': {
            'Meta': {'object_name': 'School'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'form_number': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'km_to_DEO': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'satellite_number': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'total_enrollment': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        }
    }

    complete_apps = ['edusupply']
