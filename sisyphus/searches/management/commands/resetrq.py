import django_rq
from rq import Worker
from rq.command import send_stop_job_command

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, **options):
        q = django_rq.get_queue('default')
        q.empty()
        workers = Worker.all(q.connection)
        for worker in workers:
            if worker.get_current_job():
                send_stop_job_command(q.connection, worker.get_current_job().id)
        finished = q.finished_job_registry
        for job_id in finished.get_job_ids():
            finished.remove(job_id, delete_job=True)
        failed = q.failed_job_registry
        for job_id in failed.get_job_ids():
            failed.remove(job_id, delete_job=True)
        
