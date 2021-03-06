# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 02:46
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import server.models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0007_auto_20170928_2141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hunt',
            name='private_token',
            field=models.CharField(default=server.models.generate_token, max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(8)]),
        ),
        migrations.AlterField(
            model_name='huntauthorizationtoken',
            name='token',
            field=models.CharField(default=server.models.generate_token, max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(8)]),
        ),
    ]
