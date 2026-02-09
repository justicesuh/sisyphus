from django.db import migrations


def backfill_search_user(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Search = apps.get_model('searches', 'Search')

    default_profile = UserProfile.objects.first()
    if default_profile:
        Search.objects.filter(user__isnull=True).update(user=default_profile)


class Migration(migrations.Migration):

    dependencies = [
        ('searches', '0006_search_user'),
    ]

    operations = [
        migrations.RunPython(backfill_search_user, migrations.RunPython.noop),
    ]
