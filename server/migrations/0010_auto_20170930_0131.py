# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-30 05:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0009_player_hunt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='name',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together=set([('name', 'hunt')]),
        ),
    ]
