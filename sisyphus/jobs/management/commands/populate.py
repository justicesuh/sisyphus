from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job
from sisyphus.search.parsers.linkedin import LinkedInParser


class Command(BaseCommand):
    def handle(self, **options):
        parser = LinkedInParser()

        banned = Job.objects.banned()
        for job in banned:
            job.dismiss(f'{job.company.name} is banned.')
        print(f'Dismissed {len(banned)} jobs.')

        jobs = Job.objects.filter(populated=False).exclude(status=Job.DISMISSED)
        print(f'Populating {len(jobs)} jobs.')
        for job in jobs:
            parser.populate_job(job)
