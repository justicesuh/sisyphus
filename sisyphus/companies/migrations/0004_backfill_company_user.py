from django.db import migrations


def backfill_company_user(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Company = apps.get_model('companies', 'Company')

    default_profile = UserProfile.objects.first()
    if default_profile:
        Company.objects.filter(user__isnull=True).update(user=default_profile)


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0003_company_user_alter_company_linkedin_url_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_company_user, migrations.RunPython.noop),
    ]
