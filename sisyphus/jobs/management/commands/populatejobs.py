from django.core.management.base import BaseCommand

from sisyphus.jobs.tasks import populate_unpopulated_jobs


class Command(BaseCommand):
    def handle(self, **options):
        populate_unpopulated_jobs.delay()
