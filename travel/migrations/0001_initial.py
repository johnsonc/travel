# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import travel.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TravelBucketList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('is_public', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'travel_bucket_list',
            },
        ),
        migrations.CreateModel(
            name='TravelCurrency',
            fields=[
                ('iso', models.CharField(max_length=4, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('fraction', models.CharField(max_length=8, blank=True)),
                ('fraction_name', models.CharField(max_length=15, blank=True)),
                ('sign', models.CharField(max_length=4, blank=True)),
                ('alt_sign', models.CharField(max_length=4, blank=True)),
            ],
            options={
                'db_table': 'travel_currency',
            },
        ),
        migrations.CreateModel(
            name='TravelEntity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('geonameid', models.IntegerField(default=0)),
                ('code', models.CharField(max_length=6, db_index=True)),
                ('name', models.CharField(max_length=175)),
                ('full_name', models.CharField(max_length=175)),
                ('lat', models.DecimalField(null=True, max_digits=7, decimal_places=4, blank=True)),
                ('lon', models.DecimalField(null=True, max_digits=7, decimal_places=4, blank=True)),
                ('category', models.CharField(max_length=4, blank=True)),
                ('locality', models.CharField(max_length=256, blank=True)),
                ('tz', models.CharField(max_length=40, verbose_name=b'timezone', blank=True)),
                ('capital', models.ForeignKey(related_name='capital_set', blank=True, to='travel.TravelEntity', null=True)),
                ('continent', models.ForeignKey(related_name='continent_set', blank=True, to='travel.TravelEntity', null=True)),
                ('country', models.ForeignKey(related_name='country_set', blank=True, to='travel.TravelEntity', null=True)),
            ],
            options={
                'ordering': ('name',),
                'db_table': 'travel_entity',
            },
        ),
        migrations.CreateModel(
            name='TravelEntityInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iso3', models.CharField(max_length=3, blank=True)),
                ('denom', models.CharField(max_length=40, blank=True)),
                ('denoms', models.CharField(max_length=60, blank=True)),
                ('language_codes', models.CharField(max_length=100, blank=True)),
                ('phone', models.CharField(max_length=20, blank=True)),
                ('electrical', models.CharField(max_length=40, blank=True)),
                ('postal_code', models.CharField(max_length=60, blank=True)),
                ('tld', models.CharField(max_length=8, blank=True)),
                ('population', models.IntegerField(default=None, null=True, blank=True)),
                ('area', models.IntegerField(default=None, null=True, blank=True)),
                ('currency', models.ForeignKey(blank=True, to='travel.TravelCurrency', null=True)),
                ('entity', models.OneToOneField(related_name='entityinfo', to='travel.TravelEntity')),
            ],
            options={
                'db_table': 'travel_entityinfo',
            },
        ),
        migrations.CreateModel(
            name='TravelEntityType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('abbr', models.CharField(max_length=4, db_index=True)),
                ('title', models.CharField(max_length=25)),
            ],
            options={
                'db_table': 'travel_entitytype',
            },
        ),
        migrations.CreateModel(
            name='TravelFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.CharField(max_length=255)),
                ('base_dir', models.CharField(max_length=8)),
                ('ref', models.CharField(max_length=6)),
                ('thumb', models.ImageField(upload_to=travel.models.flag_upload_32, blank=True)),
                ('large', models.ImageField(upload_to=travel.models.flag_upload_128, blank=True)),
                ('svg', models.FileField(upload_to=travel.models.svg_upload, blank=True)),
                ('is_locked', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'travel_flag',
            },
        ),
        migrations.CreateModel(
            name='TravelLanguage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iso639_1', models.CharField(max_length=2, blank=True)),
                ('iso639_2', models.CharField(max_length=12, blank=True)),
                ('iso639_3', models.CharField(max_length=3, blank=True)),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='TravelLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('arrival', models.DateTimeField()),
                ('rating', models.PositiveSmallIntegerField(default=3, choices=[(1, b'&#9733;&#9733;&#9733;&#9733;&#9733;'), (2, b'&#9733;&#9733;&#9733;&#9733;'), (3, b'&#9733;&#9733;&#9733;'), (4, b'&#9733;&#9733;'), (5, b'&#9733;')])),
                ('notes', models.TextField(blank=True)),
                ('entity', models.ForeignKey(to='travel.TravelEntity')),
                ('user', models.ForeignKey(related_name='travellog_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-arrival',),
                'get_latest_by': 'arrival',
            },
        ),
        migrations.CreateModel(
            name='TravelProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access', models.CharField(default='PRO', max_length=3, choices=[('PUB', b'Public'), ('PRI', b'Private'), ('PRO', b'Protected')])),
                ('user', models.OneToOneField(related_name='travel_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'travel_profile',
            },
        ),
        migrations.AddField(
            model_name='travelentityinfo',
            name='languages',
            field=models.ManyToManyField(to='travel.TravelLanguage', blank=True),
        ),
        migrations.AddField(
            model_name='travelentityinfo',
            name='neighbors',
            field=models.ManyToManyField(to='travel.TravelEntity', blank=True),
        ),
        migrations.AddField(
            model_name='travelentity',
            name='flag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='travel.TravelFlag', null=True),
        ),
        migrations.AddField(
            model_name='travelentity',
            name='state',
            field=models.ForeignKey(related_name='state_set', blank=True, to='travel.TravelEntity', null=True),
        ),
        migrations.AddField(
            model_name='travelentity',
            name='type',
            field=models.ForeignKey(related_name='entity_set', to='travel.TravelEntityType'),
        ),
        migrations.AddField(
            model_name='travelbucketlist',
            name='entities',
            field=models.ManyToManyField(to='travel.TravelEntity'),
        ),
        migrations.AddField(
            model_name='travelbucketlist',
            name='owner',
            field=models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
