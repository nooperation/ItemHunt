# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-04-22 20:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0012_auto_20180422_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='hunt',
        ),
    ]
