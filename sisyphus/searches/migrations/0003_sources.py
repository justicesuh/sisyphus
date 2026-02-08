from django.db import migrations


def create_sources(apps, schema_editor):
    Source = apps.get_model('searches', 'Source')
    sources = [
        {'name': 'LinkedIn', 'parser': 'linkedin'},
    ]
    for source in sources:
        Source.objects.get_or_create(name=source['name'], parser=source['parser'])


class Migration(migrations.Migration):
    dependencies = [
        ('searches', '0002_searchrun'),
    ]

    operations = [
        migrations.RunPython(create_sources, migrations.RunPython.noop),
    ]
