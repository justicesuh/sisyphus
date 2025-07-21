from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job
from sisyphus.rules.models import Rule


class Command(BaseCommand):
    def handle(self, **options):
        jobs = Job.objects.banned()
        for job in jobs:
            job.dismiss(f'{job.company.name} is banned.')

        rules = Rule.objects.all()
        for rule in rules:
            if rule.operator == Rule.CONTAINS:
                jobs = Job.objects.field_contains(rule.field, rule.value)
                for job in jobs:
                    job.update_status(rule.status)
                    job.save()
