from django.core.management.base import BaseCommand

from sisyphus.jobs.models import Job


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('term')

    def handle(self, *args, **options):
        count = Job.objects.filter(status__in=[Job.Status.NEW, Job.Status.SAVED], populated=True, title__icontains=options['term']).count()
        self.stdout.write(self.style.SUCCESS(f'Found {count} jobs.'))
