# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-30 05:36
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0010_auto_20170930_0131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='uuid',
            field=models.CharField(max_length=36, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Invalid UUID', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')]),
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together=set([('uuid', 'hunt'), ('name', 'hunt')]),
        ),
    ]
