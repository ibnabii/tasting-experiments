# Generated by Django 4.2.4 on 2023-08-13 10:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasex', '0008_alter_questionorder_unique_together_panelquestion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionorder',
            name='question_set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_order', to='tasex.questionset'),
        ),
    ]
