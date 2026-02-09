from django.db import migrations


def create_locations(apps, schema_editor):
    Location = apps.get_model('jobs', 'Location')
    locations = [
        {'name': 'United States', 'geo_id': 103644278},
    ]
    for location in locations:
        Location.objects.get_or_create(name=location['name'], geo_id=location['geo_id'])


class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0012_alter_job_user'),
    ]

    operations = [
        migrations.RunPython(create_locations, migrations.RunPython.noop),
    ]
