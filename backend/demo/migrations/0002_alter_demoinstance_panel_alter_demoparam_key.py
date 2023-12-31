# Generated by Django 4.2.3 on 2023-10-04 18:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasex', '0009_answer'),
        ('demo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoinstance',
            name='panel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='tasex.panel'),
        ),
        migrations.AlterField(
            model_name='demoparam',
            name='key',
            field=models.CharField(max_length=50),
        ),
    ]
