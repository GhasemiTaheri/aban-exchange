# Generated by Django 5.0.10 on 2024-12-17 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='token_balance',
            field=models.PositiveIntegerField(default=0, verbose_name='Wallet balance'),
        ),
    ]
