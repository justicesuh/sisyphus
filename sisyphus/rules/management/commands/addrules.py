from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule


class Command(BaseCommand):
    def handle(self, **options):
        Rule.objects.get_or_create(
            name='Remove expired jobs',
            defaults={
                'field': 'raw_html',
                'operator': Rule.CONTAINS,
                'value': 'No longer accepting applications',
                'status': Job.EXPIRED
            }
        )

    terms = [
        'intern',
        'ruby on rails',
        'spring boot',
        'power bi',
        'splunk',
        'data visualization',
        'rust',
        'kubernetes',
        'data analyst',
        'tableau',
        'devops',
        'devsecops',
        'salesforce',
        'servicenow',
        'sharepoint',
        'angular',
        'powerbi',
        'c#',
        '.net',
        'support',
        'php',
        'frontend',
        'front end',
        'sdet',
        'test',
        'tutor',
        'java',
        'elixir',
        'business',
        'operations',
        'analyst',
        'front-end',
        'qa engineer',
    ]
    for term in terms:
        Rule.objects.get_or_create(
            name=f'Remove {term}',
            defaults={
                'field': 'title',
                'operator': Rule.CONTAINS,
                'value': term,
                'status': Job.DISMISSED,
            }
        )

    save_terms = [
        'python',
        'django',
        'fastapi',
        'flask',
    ]
    for term in save_terms:
        Rule.objects.get_or_create(
            name=f'Save {term}',
            defaults={
                'field': 'title',
                'operator': Rule.CONTAINS,
                'value': term,
                'status': Job.SAVED,
            }
        )
