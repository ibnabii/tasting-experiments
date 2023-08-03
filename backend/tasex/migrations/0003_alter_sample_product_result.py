# Generated by Django 4.2.3 on 2023-08-03 23:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasex', '0002_remove_panel_is_active_panel_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samplesp', to='tasex.product'),
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField(editable=False, null=True)),
                ('odd_sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='tasex.sample')),
                ('panel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='tasex.panel')),
                ('sample_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='tasex.sampleset')),
            ],
        ),
    ]
