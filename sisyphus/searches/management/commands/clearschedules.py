import django_rq
from django.core.management.base import BaseCommand
from rq_scheduler import Scheduler


class Command(BaseCommand):
    def handle(self, **options):
        scheduler = Scheduler(connection=django_rq.get_connection())
        for scheduled_job in scheduler.get_jobs():
                scheduler.cancel(scheduled_job)
