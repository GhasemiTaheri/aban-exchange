# Generated by Django 5.0.10 on 2024-12-18 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_token_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='token_balance',
            field=models.PositiveIntegerField(default=0, verbose_name='Token balance'),
        ),
    ]