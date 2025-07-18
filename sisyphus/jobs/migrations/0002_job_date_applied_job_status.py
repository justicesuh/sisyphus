# Generated by Django 5.2.4 on 2025-07-19 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='date_applied',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='status',
            field=models.CharField(choices=[('interested', 'Interested'), ('dismissed', 'Dismissed'), ('applied', 'Applied'), ('rejected', 'Rejected'), ('interview', 'Interview'), ('offer', 'Offer'), ('accepted', 'Accepted'), ('withdrawn', 'Withdrawn')], default='interested', max_length=10),
        ),
    ]
