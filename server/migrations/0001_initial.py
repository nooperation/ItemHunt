# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-23 19:12
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Hunt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('public_token', models.CharField(max_length=64, unique=True)),
                ('private_token', models.CharField(max_length=64, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True, validators=[django.core.validators.RegexValidator(code='invalid object key', message='Invalid object key', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')])),
                ('name', models.CharField(max_length=255)),
                ('type', models.IntegerField(choices=[(0, 'Credit'), (1, 'Prize')], default=0)),
                ('position_x', models.FloatField()),
                ('position_y', models.FloatField()),
                ('position_z', models.FloatField()),
                ('points', models.IntegerField()),
                ('enabled', models.BooleanField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_uuid', message='Invalid UUID', regex='^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')])),
                ('name', models.CharField(max_length=64)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField()),
                ('player_x', models.FloatField()),
                ('player_y', models.FloatField()),
                ('player_z', models.FloatField()),
                ('item_x', models.FloatField()),
                ('item_y', models.FloatField()),
                ('item_z', models.FloatField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='server.Player')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='server.Region')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='server.Region'),
        ),
    ]