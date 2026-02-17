from typing import Any

from django.core.management.base import BaseCommand

from sisyphus.accounts.models import User
from sisyphus.jobs.models import Job


class Command(BaseCommand):
    help = 'Calculate scores for all jobs that do not have a score'

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument('email', type=str, help='Email address of the user whose resume to use')

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the score calculation command."""
        email = options['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'User with email "{email}" not found'))
            return

        try:
            resume = user.profile.resume
        except AttributeError:
            self.stderr.write(self.style.ERROR(f'No resume found for user "{email}"'))
            return

        jobs = Job.objects.filter(status=Job.Status.NEW, score__isnull=True, populated=True)
        count = jobs.count()
        self.stdout.write(f'Found {count} jobs to score')

        for job in jobs:
            job.calculate_score(resume)

        self.stdout.write(self.style.SUCCESS(f'Queued {count} jobs for scoring'))
