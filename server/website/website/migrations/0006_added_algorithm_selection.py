# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-09-10 04:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_adding_session_knob'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='algorithm',
            field=models.IntegerField(choices=[(1, 'Ottertune Default'), (2, 'Algorithm 1'), (3, 'Algorithm 2'), (4, 'Algorithm 3')], default=1),
        ),
        migrations.AlterField(
            model_name='pipelinedata',
            name='pipeline_run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.PipelineRun', verbose_name='group'),
        ),
    ]
