# Generated by Django 4.2.3 on 2023-08-03 23:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasex', '0004_alter_sample_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='result',
            name='panel',
        ),
    ]
