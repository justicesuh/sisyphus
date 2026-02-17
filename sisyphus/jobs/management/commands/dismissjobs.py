from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job


class Command(BaseCommand):
    help = 'Dismiss scored jobs below given threshold.'

    def add_arguments(self, parser):
        parser.add_argument('threshold')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, **options):
        threshold = options['threshold']
        jobs = Job.objects.filter(status=Job.Status.NEW, score__lte=threshold)
        self.stdout.write(self.style.SUCCESS(f'Found {len(jobs)} jobs below {threshold}.'))

        if options['dry_run']:
            return
        
        for job in jobs:
            job.update_status(Job.Status.FILTERED)
        self.stdout.write(self.style.SUCCESS(f'Filtered {len(jobs)} jobs.'))
