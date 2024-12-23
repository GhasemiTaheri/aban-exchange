# Generated by Django 5.0.10 on 2024-12-18 22:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='archiveorder',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_related', related_query_name='%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='Order owner'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_related', related_query_name='%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='Order owner'),
        ),
    ]
