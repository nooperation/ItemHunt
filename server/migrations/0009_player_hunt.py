# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-30 05:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0008_auto_20170928_2246'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='hunt',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='server.Hunt'),
            preserve_default=False,
        ),
    ]