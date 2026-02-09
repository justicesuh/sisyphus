from django.db import migrations


def backfill_job_user(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    Job = apps.get_model('jobs', 'Job')

    default_profile = UserProfile.objects.first()

    for job in Job.objects.filter(user__isnull=True).select_related('search_run__search'):
        if job.search_run and job.search_run.search and job.search_run.search.user:
            job.user = job.search_run.search.user
        elif default_profile:
            job.user = default_profile
        job.save(update_fields=['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0010_job_user_alter_job_url_job_unique_job_url_per_user'),
        ('searches', '0008_alter_search_user'),
    ]

    operations = [
        migrations.RunPython(backfill_job_user, migrations.RunPython.noop),
    ]
