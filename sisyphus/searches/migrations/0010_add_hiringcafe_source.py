from django.db import migrations


def create_hiringcafe(apps, schema_editor):
    Source = apps.get_model('searches', 'Source')
    sources = [
        {'name': 'HiringCafe', 'parser': 'hiringcafe'},
    ]
    for source in sources:
        Source.objects.get_or_create(name=source['name'], parser=source['parser'])


class Migration(migrations.Migration):
    dependencies = [
        ('searches', '0009_search_schedule'),
    ]

    operations = [
        migrations.RunPython(create_hiringcafe, migrations.RunPython.noop),
    ]
